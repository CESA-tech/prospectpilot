from datetime import datetime
from .models import Session, Lead


def save_lead(company_name: str, company_domain: str, research: dict, draft: dict, contact: dict = None) -> Lead:
    with Session() as session:
        lead = Lead(
            company_name=company_name,
            company_domain=company_domain,
            research=research,
            draft_subject=draft.get("subject"),
            draft_body=draft.get("body"),
            contact_name=f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() if contact else "",
            contact_email=contact.get("value", "") if contact else "",
            contact_position=contact.get("position", "") if contact else "",
            status="draft"
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)
        print(f"[db] Lead kaydedildi → ID: {lead.id}, Şirket: {lead.company_name}")
        return lead


def update_lead_draft(lead_id: int, draft: dict):
    with Session() as session:
        lead = session.get(Lead, lead_id)
        if lead:
            lead.draft_subject = draft.get("subject")
            lead.draft_body = draft.get("body")
            session.commit()
            print(f"[db] Lead #{lead_id} taslak güncellendi.")


def update_status(lead_id: int, status: str):
    with Session() as session:
        lead = session.get(Lead, lead_id)
        if lead:
            lead.status = status
            if status == "sent" and not lead.sent_at:
                lead.sent_at = datetime.utcnow()
            session.commit()
            print(f"[db] Lead #{lead_id} → {status}")


def increment_follow_up(lead_id: int):
    with Session() as session:
        lead = session.get(Lead, lead_id)
        if lead:
            lead.follow_up_count = (lead.follow_up_count or 0) + 1
            lead.last_follow_up_at = datetime.utcnow()
            session.commit()
            print(f"[db] Lead #{lead_id} → follow-up #{lead.follow_up_count}")


def list_leads(status: str = None) -> list:
    with Session() as session:
        query = session.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        return query.order_by(Lead.created_at.desc()).all()


def get_stats() -> dict:
    with Session() as session:
        total = session.query(Lead).count()
        draft = session.query(Lead).filter(Lead.status == "draft").count()
        sent = session.query(Lead).filter(Lead.status == "sent").count()
        replied = session.query(Lead).filter(Lead.status == "replied").count()

        fu_pending = session.query(Lead).filter(
            Lead.status == "sent",
            Lead.follow_up_count < 2
        ).count()
        fu_done = session.query(Lead).filter(
            Lead.status == "sent",
            Lead.follow_up_count >= 2
        ).count()

        return {
            "total": total,
            "draft": draft,
            "sent": sent,
            "replied": replied,
            "fu_pending": fu_pending,
            "fu_done": fu_done,
        }


def reset_all_leads():
    with Session() as session:
        session.query(Lead).delete()
        session.commit()
