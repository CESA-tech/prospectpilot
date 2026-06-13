import sys
import os
import json
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from dotenv import load_dotenv
from src.agents.research_agent import research_company
from src.agents.draft_agent import draft_email
from src.tools.enrichment import select_contact
from src.tools.email_sender import send_email
from src.db.models import init_db
from src.db.crud import save_lead, update_status, update_lead_draft

load_dotenv()

STYLES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'outreach_styles.json')
LEADS_CSV = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'leads.csv')

SENDER_NAME = os.getenv("SENDER_NAME", "Alex")
SENDER_ROLE = os.getenv("SENDER_ROLE", "AI Automation Consultant")
SERVICE_OFFERED = os.getenv("SERVICE_OFFERED", "AI-powered outreach automation")

MAX_RETRIES = 2


# --- State ---

class ProspectState(TypedDict):
    company_name: str
    domain: str
    research: Optional[dict]
    contact: Optional[dict]
    draft: Optional[dict]
    approved: bool
    save_as_draft: bool
    sent: bool
    lead_id: Optional[int]
    error: Optional[str]
    retry_count: int


# --- Nodes ---

def research_node(state: ProspectState) -> dict:
    attempt = state.get("retry_count", 0) + 1
    print(f"\n[1/5] '{state['company_name']}' araştırılıyor... (deneme {attempt}/{MAX_RETRIES})\n")
    try:
        research = research_company(state["company_name"])
    except Exception as e:
        print(f"  [!] Araştırma başarısız: {e}")
        return {"error": str(e), "retry_count": attempt, "research": None, "domain": ""}

    print("Araştırma tamamlandı.")

    found_domain = research.get("domain", "")
    if found_domain:
        print(f"\nAjan domain buldu: {found_domain}")
        override = input("Doğruysa Enter, değiştirmek istersen yaz: ").strip()
        domain = override if override else found_domain
    else:
        domain = input("\nDomain bulunamadı. Elle gir veya Enter ile atla: ").strip()

    research["domain"] = domain
    return {"research": research, "domain": domain, "error": None, "retry_count": attempt}


def enrich_node(state: ProspectState) -> dict:
    print(f"\n[2/5] Kişi aranıyor...\n")
    contact = select_contact(state["domain"])
    return {"contact": contact}


def draft_node(state: ProspectState) -> dict:
    print(f"\n[3/5] Email taslağı yazılıyor...\n")
    draft = draft_email(
        state["research"],
        SENDER_NAME,
        SENDER_ROLE,
        SERVICE_OFFERED,
        contact=state["contact"]
    )
    return {"draft": draft}


def approval_node(state: ProspectState) -> dict:
    draft = state["draft"]

    while True:
        print("\n" + "=" * 60)
        print(f"SUBJECT: {draft['subject']}\n")
        print(f"BODY:\n{draft['body']}\n")
        print(f"PERSONALIZATION: {draft['personalization_used']}")
        print("=" * 60)

        with open(STYLES_PATH, encoding="utf-8") as f:
            styles = json.load(f)["styles"]

        print("\nNe yapmak istersin?")
        for i, style in enumerate(styles, 1):
            print(f"  [{i}] {style['label']}")
        print("  [D] Anlık düzenleme (kaydetmeden)")
        print("  [Y] Yeni stil oluştur ve kaydet")
        print("  [E] Onayla ve gönder")
        print("  [K] Taslak olarak kaydet (göndermeden)")
        print("  [H] İptal et")

        choice = input("\nSeçim: ").strip().lower()

        if choice == "e":
            return {"draft": draft, "approved": True}
        elif choice == "k":
            print("\nTaslak olarak kaydedildi.")
            return {"draft": draft, "approved": False, "save_as_draft": True}
        elif choice == "h":
            return {"approved": False}
        elif choice == "d":
            instruction = input("Talimat: ").strip()
            if instruction:
                draft = draft_email(state["research"], SENDER_NAME, SENDER_ROLE,
                                    SERVICE_OFFERED, instruction, state["contact"])
        elif choice == "y":
            label = input("Stil adı (Türkçe, menüde görünecek): ").strip()
            instruction = input("Talimat (İngilizce, Claude'a verilecek): ").strip()
            if label and instruction:
                new_style = {"id": label.lower().replace(" ", "_"), "label": label, "instruction": instruction}
                with open(STYLES_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                data["styles"].append(new_style)
                with open(STYLES_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n  '{label}' stili kaydedildi. Uygulanıyor...\n")
                draft = draft_email(state["research"], SENDER_NAME, SENDER_ROLE,
                                    SERVICE_OFFERED, instruction, state["contact"])
            else:
                print("  Stil adı ve talimat boş olamaz.")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(styles):
                draft = draft_email(state["research"], SENDER_NAME, SENDER_ROLE,
                                    SERVICE_OFFERED, styles[idx]["instruction"], state["contact"])


def send_node(state: ProspectState) -> dict:
    print(f"\n[5/5] Email gönderiliyor...\n")
    contact = state["contact"]
    draft = state["draft"]
    to_email = contact["value"] if contact else None

    if not to_email:
        print("Alıcı email adresi yok, gönderilmedi.")
        return {"sent": False}

    success = send_email(to_email, draft["subject"], draft["body"])
    return {"sent": success}


def save_node(state: ProspectState) -> dict:
    print(f"\n[4/5] Kaydediliyor...\n")
    init_db()

    existing_id = state.get("lead_id")
    status = "sent" if state.get("sent") else "approved" if state.get("approved") else "draft"

    if existing_id:
        choice = input("Mevcut draftın üstüne mi kaydet? (e = üstüne yaz / h = yeni draft): ").strip().lower()
        if choice == "e":
            update_lead_draft(existing_id, state["draft"])
            update_status(existing_id, status)
            return {"lead_id": existing_id}

    lead = save_lead(
        state["company_name"],
        state["domain"],
        state["research"],
        state["draft"],
        state["contact"]
    )
    update_status(lead.id, status)
    return {"lead_id": lead.id}


# --- Routing ---

def after_research(state: ProspectState) -> str:
    """Research başarısız → retry. Domain yok → direkt draft. Domain var → enrich."""
    if state.get("error"):
        if state.get("retry_count", 0) < MAX_RETRIES:
            print(f"  Yeniden deneniyor...")
            return "research"
        else:
            print(f"  Maksimum deneme sayısına ulaşıldı, atlanıyor.")
            return END
    return "enrich" if state.get("domain") else "draft"


def should_send(state: ProspectState) -> str:
    if state.get("approved"):
        return "send"
    elif state.get("save_as_draft"):
        return "save"
    else:
        return END  # iptal edildi, kaydetme


# --- Graph ---

def build_graph():
    graph = StateGraph(ProspectState)

    graph.add_node("research", research_node)
    graph.add_node("enrich", enrich_node)
    graph.add_node("draft", draft_node)
    graph.add_node("approval", approval_node)
    graph.add_node("send", send_node)
    graph.add_node("save", save_node)

    graph.set_entry_point("research")
    graph.add_conditional_edges("research", after_research, {
        "research": "research",
        "enrich": "enrich",
        "draft": "draft",
        END: END
    })
    graph.add_edge("enrich", "draft")
    graph.add_edge("draft", "approval")
    graph.add_conditional_edges("approval", should_send, {
        "send": "send",
        "save": "save",
        END: END
    })
    graph.add_edge("send", "save")
    graph.add_edge("save", END)

    return graph.compile()


def run(company_name: str):
    """Tek şirket için pipeline çalıştır."""
    init_db()
    app = build_graph()
    initial_state = ProspectState(
        company_name=company_name,
        domain="",
        research=None,
        contact=None,
        draft=None,
        approved=False,
        save_as_draft=False,
        sent=False,
        lead_id=None,
        error=None,
        retry_count=0
    )
    final_state = app.invoke(initial_state)

    print("\n" + "=" * 60)
    if final_state.get("sent"):
        print(f"Tamamlandı. Email gönderildi. Lead ID: {final_state['lead_id']}")
    elif final_state.get("save_as_draft"):
        print(f"Taslak kaydedildi. Lead ID: {final_state['lead_id']}")
    else:
        print("İptal edildi, kaydedilmedi.")
    print("=" * 60)


def resume_lead(lead_id: int):
    """Kayıtlı bir draft lead'i yükleyip approval'dan devam ettir."""
    from src.db.models import Session, Lead as LeadModel

    init_db()
    with Session() as session:
        lead = session.get(LeadModel, lead_id)
        if not lead:
            print(f"Lead #{lead_id} bulunamadı.")
            return
        if lead.status not in ("draft",):
            print(f"Lead #{lead_id} zaten '{lead.status}' durumunda, devam edilemez.")
            return

        # DB'den state'i yeniden oluştur
        contact = {
            "first_name": lead.contact_name.split()[0] if lead.contact_name else "",
            "last_name": " ".join(lead.contact_name.split()[1:]) if lead.contact_name else "",
            "value": lead.contact_email,
            "position": lead.contact_position
        } if lead.contact_email else None

        state = ProspectState(
            company_name=lead.company_name,
            domain=lead.company_domain or "",
            research=lead.research or {},
            contact=contact,
            draft={"subject": lead.draft_subject, "body": lead.draft_body, "personalization_used": ""},
            approved=False,
            save_as_draft=False,
            sent=False,
            lead_id=lead_id,
            error=None,
            retry_count=0
        )

    # Sadece approval → send → save kısmını çalıştır
    graph = StateGraph(ProspectState)
    graph.add_node("approval", approval_node)
    graph.add_node("send", send_node)
    graph.add_node("save", save_node)
    graph.set_entry_point("approval")
    graph.add_conditional_edges("approval", should_send, {
        "send": "send",
        "save": "save",
        END: END
    })
    graph.add_edge("send", "save")
    graph.add_edge("save", END)
    app = graph.compile()

    final_state = app.invoke(state)

    print("\n" + "=" * 60)
    if final_state.get("sent"):
        print(f"Email gönderildi. Lead #{lead_id}")
    elif final_state.get("save_as_draft"):
        print(f"Taslak güncellendi. Lead #{lead_id}")
    else:
        print("İptal edildi.")
    print("=" * 60)


def run_batch():
    """CSV'den şirket listesini okuyup sırayla işle."""
    if not os.path.exists(LEADS_CSV):
        print(f"CSV bulunamadı: {LEADS_CSV}")
        return

    with open(LEADS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"{len(rows)} şirket bulundu.\n")

    for i, row in enumerate(rows, 1):
        company = row.get("company", "").strip()
        if not company:
            continue
        print(f"\n{'='*60}")
        print(f"[{i}/{len(rows)}] {company}")
        print(f"{'='*60}")
        run(company)


if __name__ == "__main__":
    company = input("Şirket adı: ").strip()
    run(company)
