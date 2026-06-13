import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.db.models import init_db, Session, Lead
from src.db.crud import get_stats, update_status, reset_all_leads, increment_follow_up, save_lead
from src.tools.email_sender import send_email
from src.tools.enrichment import fetch_contacts, filter_contacts, get_departments, DEPARTMENT_LABELS
from src.tools.follow_up import check_all_replies, get_due_for_followup, _follow_up_base_instruction
from src.agents.research_agent import research_company
from src.agents.draft_agent import draft_email

STYLES_PATH = os.path.join(os.path.dirname(__file__), "config", "outreach_styles.json")
SENDER_NAME = os.getenv("SENDER_NAME", "Alex")
SENDER_ROLE = os.getenv("SENDER_ROLE", "AI Automation Consultant")
SERVICE_OFFERED = os.getenv("SERVICE_OFFERED", "AI-powered outreach automation")

init_db()

st.set_page_config(page_title="ProspectPilot", layout="wide")

st.markdown("""
<style>
    [data-testid="stStatusWidget"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("ProspectPilot")

tab_new, tab_batch, tab_dashboard, tab_leads, tab_followup = st.tabs([
    "New Lead", "Batch Process", "Dashboard", "Leads", "Follow-ups"
])


# ── helpers ───────────────────────────────────────────────────────────────────

def load_styles():
    with open(STYLES_PATH, encoding="utf-8") as f:
        return json.load(f)["styles"]


def days_ago(dt):
    if not dt:
        return "—"
    diff = (datetime.utcnow() - dt).days
    return "today" if diff == 0 else f"{diff} days ago"


def get_leads(status_filter=None):
    with Session() as session:
        q = session.query(Lead)
        if status_filter and status_filter != "All":
            q = q.filter(Lead.status == status_filter.lower())
        return q.order_by(Lead.created_at.desc()).all()


def reset_new_lead():
    for key in ["nl_stage", "nl_company", "nl_research", "nl_domain",
                "nl_contacts", "nl_contact", "nl_draft"]:
        st.session_state.pop(key, None)


# ── TAB 1: New Lead ───────────────────────────────────────────────────────────

with tab_new:
    stage = st.session_state.get("nl_stage", "input")

    if stage != "input":
        if st.button("Reset / Start over", key="nl_reset"):
            reset_new_lead()
            st.rerun()

    # ── STEP 1: Company name ──────────────────────────────────────────────────
    if stage == "input":
        st.subheader("Research a Company")
        company = st.text_input("Company name", placeholder="e.g. Linear, Vercel, Notion")
        if st.button("Research", type="primary", disabled=not company.strip()):
            st.session_state["nl_company"] = company.strip()
            st.session_state["nl_stage"] = "researching"
            st.rerun()

    # ── STEP 2: Research running ──────────────────────────────────────────────
    elif stage == "researching":
        company = st.session_state["nl_company"]
        st.info(f"Researching **{company}**...")
        with st.spinner("Research agent running (30–60 sec)..."):
            try:
                research = research_company(company)
                st.session_state["nl_research"] = research
                st.session_state["nl_domain"] = research.get("domain", "")
                st.session_state["nl_stage"] = "confirm_domain"
                st.rerun()
            except Exception as e:
                st.error(f"Research failed: {e}")
                if st.button("Retry"):
                    st.rerun()

    # ── STEP 3: Confirm domain ────────────────────────────────────────────────
    elif stage == "confirm_domain":
        research = st.session_state["nl_research"]
        company = st.session_state["nl_company"]

        st.subheader(f"{company} — Research Complete")

        with st.expander("Research summary", expanded=False):
            st.write(research.get("summary", "—"))

        st.divider()
        found_domain = st.session_state["nl_domain"]
        domain = st.text_input("Domain (edit if incorrect)", value=found_domain)

        col1, col2 = st.columns([1, 4])
        if col1.button("Continue →", type="primary"):
            st.session_state["nl_domain"] = domain.strip()
            research["domain"] = domain.strip()
            st.session_state["nl_research"] = research
            if domain.strip():
                st.session_state["nl_stage"] = "contacts"
            else:
                st.session_state["nl_stage"] = "draft"
            st.rerun()
        if col2.button("Continue without domain"):
            st.session_state["nl_domain"] = ""
            st.session_state["nl_stage"] = "draft"
            st.rerun()

    # ── STEP 4: Select contact ────────────────────────────────────────────────
    elif stage == "contacts":
        domain = st.session_state["nl_domain"]
        st.subheader("Select a Contact")

        if "nl_contacts" not in st.session_state:
            with st.spinner(f"Querying {domain}..."):
                try:
                    contacts = fetch_contacts(domain)
                    st.session_state["nl_contacts"] = contacts
                except Exception as e:
                    st.error(f"Hunter.io error: {e}")
                    contacts = []
                    st.session_state["nl_contacts"] = []

        contacts = st.session_state["nl_contacts"]

        if not contacts:
            st.warning("No contacts found for this domain.")
            if st.button("Continue without contact →"):
                st.session_state["nl_contact"] = None
                st.session_state["nl_stage"] = "draft"
                st.rerun()
        else:
            departments = get_departments(contacts)
            dept_options = ["All"] + [DEPARTMENT_LABELS.get(d, d.capitalize()) for d in departments]
            dept_keys = [None] + departments

            selected_dept_label = st.selectbox("Filter by department", dept_options)
            dept_idx = dept_options.index(selected_dept_label)
            selected_dept = dept_keys[dept_idx]

            filtered = filter_contacts(contacts, selected_dept)[:10]

            contact_labels = [
                f"{c.get('first_name', '')} {c.get('last_name', '')} — {c.get('position') or '—'} ({c.get('value', '')})"
                for c in filtered
            ]
            contact_labels_with_skip = ["Skip contact selection"] + contact_labels

            chosen = st.radio("Select contact", contact_labels_with_skip)

            if st.button("Continue →", type="primary"):
                if chosen == "Skip contact selection":
                    st.session_state["nl_contact"] = None
                else:
                    idx = contact_labels.index(chosen)
                    st.session_state["nl_contact"] = filtered[idx]
                st.session_state["nl_stage"] = "draft"
                st.rerun()

    # ── STEP 5: Generate draft ────────────────────────────────────────────────
    elif stage == "draft":
        research = st.session_state["nl_research"]
        contact = st.session_state.get("nl_contact")

        if "nl_draft" not in st.session_state:
            with st.spinner("Writing email draft..."):
                draft = draft_email(research, SENDER_NAME, SENDER_ROLE, SERVICE_OFFERED, contact=contact)
                st.session_state["nl_draft"] = draft
            st.rerun()
        else:
            st.session_state["nl_stage"] = "review"
            st.rerun()

    # ── STEP 6: Review & approve ──────────────────────────────────────────────
    elif stage == "review":
        research = st.session_state["nl_research"]
        contact = st.session_state.get("nl_contact")
        draft = st.session_state["nl_draft"]
        company = st.session_state["nl_company"]
        domain = st.session_state.get("nl_domain", "")

        st.subheader(f"{company} — Draft Ready")

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.write("**Saved styles:**")
            styles = load_styles()
            for style in styles:
                if st.button(style["label"], key=f"style_{style['id']}"):
                    with st.spinner("Rewriting..."):
                        new_draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                                SERVICE_OFFERED, style["instruction"], contact)
                    st.session_state["nl_draft"] = new_draft
                    st.rerun()

            st.divider()
            st.write("**Quick edit** (not saved):")
            custom_instruction = st.text_input("Instruction",
                                               placeholder="e.g. Make it shorter, no emojis",
                                               key="nl_custom_inst")
            if st.button("Apply"):
                if custom_instruction.strip():
                    with st.spinner("Rewriting..."):
                        new_draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                                SERVICE_OFFERED, custom_instruction, contact)
                    st.session_state["nl_draft"] = new_draft
                    st.rerun()

            st.divider()
            st.write("**Create & save new style:**")
            new_style_label = st.text_input("Style name (shown in menu)",
                                            placeholder="e.g. Warm and short",
                                            key="nl_new_style_label")
            new_style_inst = st.text_input("Instruction (given to Claude)",
                                           placeholder="e.g. Keep it warm and under 3 sentences",
                                           key="nl_new_style_inst")
            if st.button("Save & Apply"):
                if new_style_label.strip() and new_style_inst.strip():
                    new_style = {
                        "id": new_style_label.strip().lower().replace(" ", "_"),
                        "label": new_style_label.strip(),
                        "instruction": new_style_inst.strip()
                    }
                    with open(STYLES_PATH, encoding="utf-8") as f:
                        styles_data = json.load(f)
                    styles_data["styles"].append(new_style)
                    with open(STYLES_PATH, "w", encoding="utf-8") as f:
                        json.dump(styles_data, f, indent=2, ensure_ascii=False)
                    with st.spinner("Style saved, applying..."):
                        new_draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                                SERVICE_OFFERED, new_style_inst.strip(), contact)
                    st.session_state["nl_draft"] = new_draft
                    st.success(f"Style '{new_style_label}' saved.")
                    st.rerun()
                else:
                    st.warning("Style name and instruction cannot be empty.")

        with col_right:
            st.write(f"**Subject:** {draft['subject']}")
            edited_body = st.text_area("Body (editable)", value=draft["body"], height=300)
            if edited_body != draft["body"]:
                st.session_state["nl_draft"] = {**draft, "body": edited_body}
                draft = st.session_state["nl_draft"]

            if contact:
                st.caption(f"Recipient: {contact.get('first_name', '')} {contact.get('last_name', '')} — {contact.get('value', '')}")

        st.divider()
        btn1, btn2, btn3 = st.columns([1, 1, 4])

        if btn1.button("Approve & Send", type="primary"):
            to_email = contact["value"] if contact else None
            if not to_email:
                st.error("No recipient email. No contact was selected.")
            else:
                with st.spinner("Sending..."):
                    ok = send_email(to_email, draft["subject"], draft["body"])
                if ok:
                    lead = save_lead(company, domain, research, draft, contact)
                    update_status(lead.id, "sent")
                    st.success(f"Email sent → {to_email}")
                    st.session_state["nl_stage"] = "done"
                    st.rerun()
                else:
                    st.error("Failed to send.")

        if btn2.button("Save as Draft"):
            lead = save_lead(company, domain, research, draft, contact)
            st.success(f"Draft saved. Lead ID: {lead.id}")
            st.session_state["nl_stage"] = "done"
            st.rerun()

    # ── STEP 7: Done ──────────────────────────────────────────────────────────
    elif stage == "done":
        st.success("Done.")
        st.write("Track your leads in the Leads tab.")
        if st.button("Start new lead"):
            reset_new_lead()
            st.rerun()


# ── TAB 2: Batch Process ──────────────────────────────────────────────────────

with tab_batch:
    st.subheader("Batch Process from CSV")
    st.caption("Research, contact finding, and draft writing run automatically for each company. Drafts appear in the Leads tab for your review.")

    uploaded = st.file_uploader("Upload CSV (must have 'company' and 'domain' columns)", type="csv")

    if uploaded:
        import pandas as pd
        import io
        df = pd.read_csv(io.StringIO(uploaded.read().decode("utf-8")))
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("Start Batch", type="primary"):
            progress = st.progress(0)
            status_text = st.empty()
            errors = []

            rows = df.to_dict("records")
            for i, row in enumerate(rows):
                company = str(row.get("company", "")).strip()
                domain_hint = str(row.get("domain", "")).strip()
                if not company:
                    continue

                status_text.write(f"**{i+1}/{len(rows)}** — Processing {company}...")

                try:
                    research = research_company(company)
                    if domain_hint:
                        research["domain"] = domain_hint

                    domain = research.get("domain", "")
                    contact = None
                    if domain:
                        contacts = fetch_contacts(domain)
                        if contacts:
                            contact = contacts[0]

                    draft = draft_email(research, SENDER_NAME, SENDER_ROLE, SERVICE_OFFERED, contact=contact)
                    lead = save_lead(company, domain, research, draft, contact)
                    status_text.write(f"✓ {company} → draft saved (ID: {lead.id})")

                except Exception as e:
                    errors.append(f"{company}: {e}")
                    status_text.write(f"✗ {company} — error: {e}")

                progress.progress((i + 1) / len(rows))

            progress.empty()
            if errors:
                st.warning(f"{len(errors)} error(s):\n" + "\n".join(errors))
            st.success("Done. Review and approve drafts in the Leads tab.")


# ── TAB 3: Dashboard ──────────────────────────────────────────────────────────

with tab_dashboard:
    stats = get_stats()
    sent = stats["sent"]
    replied = stats["replied"]
    reply_rate = round((replied / sent) * 100) if sent > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Leads", stats["total"])
    c2.metric("Sent", sent)
    c3.metric("Replied", replied)
    c4.metric("Reply Rate", f"{reply_rate}%")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Follow-up Status")
        st.write(f"Pending: **{stats['fu_pending']}**")
        st.write(f"Completed: **{stats['fu_done']}**")
        st.write(f"Drafts: **{stats['draft']}**")

    with col_b:
        st.subheader("Danger Zone")
        if st.button("Reset All Leads", type="secondary"):
            st.session_state["confirm_reset"] = True

        if st.session_state.get("confirm_reset"):
            st.warning(f"**{stats['total']} lead(s) will be deleted.** This cannot be undone.")
            col1, col2 = st.columns(2)
            if col1.button("Yes, delete", type="primary"):
                reset_all_leads()
                st.session_state["confirm_reset"] = False
                st.success("All leads deleted.")
                st.rerun()
            if col2.button("Cancel"):
                st.session_state["confirm_reset"] = False
                st.rerun()


# ── TAB 4: Leads ──────────────────────────────────────────────────────────────

with tab_leads:
    col_filter, _ = st.columns([2, 6])
    with col_filter:
        status_filter = st.selectbox("Filter", ["All", "Draft", "Sent", "Replied"], key="leads_filter")

    leads = get_leads(status_filter)

    if not leads:
        st.info("No leads found.")
    else:
        import pandas as pd
        rows = [{
            "ID": l.id,
            "Company": l.company_name,
            "Contact": l.contact_name or "—",
            "Status": l.status,
            "Sent": days_ago(l.sent_at),
            "F/U": f"{l.follow_up_count or 0}/2" if l.status in ("sent", "replied") else "—",
            "Subject": (l.draft_subject or "")[:50],
        } for l in leads]

        selected = st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        sel_rows = selected.get("selection", {}).get("rows", [])
        if sel_rows:
            lead = leads[sel_rows[0]]
            st.divider()

            left, right = st.columns([1, 1])
            with left:
                st.subheader(lead.company_name)
                st.write(f"**Contact:** {lead.contact_name or '—'} — {lead.contact_email or '—'}")
                st.write(f"**Status:** `{lead.status}`")
                if lead.sent_at:
                    st.write(f"**Sent:** {days_ago(lead.sent_at)}")
                    st.write(f"**Follow-up:** {lead.follow_up_count or 0}/2")
            with right:
                st.write(f"**Subject:** {lead.draft_subject or '—'}")
                st.text_area("Body", value=lead.draft_body or "—", height=200,
                             disabled=True, label_visibility="collapsed")

            st.divider()
            b1, b2, b3 = st.columns([1, 1, 4])

            if lead.status == "draft":
                if b1.button("Approve & Send", type="primary", key="leads_send"):
                    if not lead.contact_email:
                        st.error("No recipient email.")
                    else:
                        with st.spinner("Sending..."):
                            ok = send_email(lead.contact_email, lead.draft_subject, lead.draft_body)
                        if ok:
                            update_status(lead.id, "sent")
                            st.success(f"Sent → {lead.contact_email}")
                            st.rerun()
                        else:
                            st.error("Failed to send.")

            if lead.status == "sent":
                if b1.button("Mark as Replied", type="primary", key="leads_replied"):
                    update_status(lead.id, "replied")
                    st.success("Marked as replied.")
                    st.rerun()

            if b2.button("Delete", key="leads_delete"):
                st.session_state[f"del_{lead.id}"] = True

            if st.session_state.get(f"del_{lead.id}"):
                st.warning(f"Delete **{lead.company_name}**?")
                ca, cb = st.columns([1, 5])
                if ca.button("Yes", key="del_yes"):
                    with Session() as session:
                        l = session.get(Lead, lead.id)
                        if l:
                            session.delete(l)
                            session.commit()
                    st.session_state.pop(f"del_{lead.id}", None)
                    st.success("Deleted.")
                    st.rerun()
                if cb.button("Cancel", key="del_no"):
                    st.session_state.pop(f"del_{lead.id}", None)
                    st.rerun()

        st.caption("F/U = Follow-up count (sent / max 2)")


# ── TAB 5: Follow-ups ─────────────────────────────────────────────────────────

with tab_followup:
    if st.button("Check for Replies"):
        with st.spinner("Checking Gmail..."):
            replied_list = check_all_replies()
        if replied_list:
            st.success(f"Replies received from: {', '.join(replied_list)}")
        else:
            st.info("No new replies.")

    st.divider()
    st.subheader("Due for Follow-up")
    due = get_due_for_followup()

    if not due:
        st.info("No leads due for follow-up.")
    else:
        for lead, follow_up_no, days_since in due:
            with st.expander(f"{lead.company_name} — Follow-up #{follow_up_no} (sent {days_since} days ago)"):
                contact = {
                    "first_name": (lead.contact_name or "").split()[0],
                    "last_name": " ".join((lead.contact_name or "").split()[1:]),
                    "value": lead.contact_email or "",
                    "position": lead.contact_position or ""
                }
                research = lead.research or {"company_name": lead.company_name}
                state_key = f"fu_draft_{lead.id}"

                if state_key not in st.session_state:
                    base = _follow_up_base_instruction(follow_up_no, days_since)
                    with st.spinner("Preparing draft..."):
                        draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                            SERVICE_OFFERED, base, contact)
                    st.session_state[state_key] = draft

                draft = st.session_state[state_key]
                st.write(f"**Subject:** {draft['subject']}")
                new_body = st.text_area("Body", value=draft["body"], height=150, key=f"fu_body_{lead.id}")

                fc1, fc2 = st.columns([1, 4])
                if fc1.button("Send", key=f"fu_send_{lead.id}", type="primary"):
                    with st.spinner("Sending..."):
                        ok = send_email(lead.contact_email, draft["subject"], new_body)
                    if ok:
                        increment_follow_up(lead.id)
                        st.session_state.pop(state_key, None)
                        st.success(f"Follow-up #{follow_up_no} sent.")
                        st.rerun()
                    else:
                        st.error("Failed to send.")

                if fc2.button("Regenerate", key=f"fu_regen_{lead.id}"):
                    base = _follow_up_base_instruction(follow_up_no, days_since)
                    with st.spinner("Rewriting..."):
                        new_draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                                SERVICE_OFFERED, base, contact)
                    st.session_state[state_key] = new_draft
                    st.rerun()
