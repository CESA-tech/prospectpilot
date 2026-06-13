import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.db.models import Session, Lead, init_db
from src.db.crud import update_status, increment_follow_up
from src.agents.draft_agent import draft_email
from src.tools.email_sender import send_email
from src.tools.reply_detector import check_reply

FOLLOW_UP_SCHEDULE = {1: 3, 2: 7}  # follow-up no → kaç gün sonra gönderilir

STYLES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'outreach_styles.json')

SENDER_NAME = os.getenv("SENDER_NAME", "Alex")
SENDER_ROLE = os.getenv("SENDER_ROLE", "AI Automation Consultant")
SERVICE_OFFERED = os.getenv("SERVICE_OFFERED", "AI-powered outreach automation")


def _follow_up_base_instruction(follow_up_no: int, days_since: int) -> str:
    """Follow-up numarasına göre temel talimat. Stil üstüne eklenir."""
    if follow_up_no == 1:
        return (
            f"This is follow-up #1. The initial email was sent {days_since} days ago with no reply. "
            "Keep it short (2-3 sentences). Briefly reference the previous email. "
            "Ask a simple yes/no question to lower the barrier. "
        )
    else:
        return (
            f"This is follow-up #2 (final). The initial email was sent {days_since} days ago with no reply. "
            "Very short — 2 sentences max. "
            "Mention this is the last follow-up. Offer a concrete next step (e.g. a quick 15-min call). "
        )


def _approval_menu(draft: dict, research: dict, contact: dict,
                   follow_up_no: int, days_since: int) -> tuple[dict, bool]:
    """
    Follow-up onay menüsü. (draft, should_send) döndürür.
    İlk drafttaki menünün aynısı: stiller, anlık düzenleme, yeni stil, gönder, atla.
    """
    base_instruction = _follow_up_base_instruction(follow_up_no, days_since)

    while True:
        print("\n" + "=" * 60)
        print(f"SUBJECT: {draft['subject']}\n")
        print(f"BODY:\n{draft['body']}\n")
        print("=" * 60)

        with open(STYLES_PATH, encoding="utf-8") as f:
            styles = json.load(f)["styles"]

        print("\nNe yapmak istersin?")
        for i, style in enumerate(styles, 1):
            print(f"  [{i}] {style['label']}")
        print("  [D] Anlık düzenleme (kaydetmeden)")
        print("  [Y] Yeni stil oluştur ve kaydet")
        print("  [E] Onayla ve gönder")
        print("  [H] Bu lead'i atla")

        choice = input("\nSeçim: ").strip().lower()

        if choice == "e":
            return draft, True

        elif choice == "h":
            return draft, False

        elif choice == "d":
            instruction = input("Talimat: ").strip()
            if instruction:
                draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                    SERVICE_OFFERED, instruction, contact)

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
                full_instruction = base_instruction + instruction
                draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                    SERVICE_OFFERED, full_instruction, contact)
            else:
                print("  Stil adı ve talimat boş olamaz.")

        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(styles):
                full_instruction = base_instruction + styles[idx]["instruction"]
                draft = draft_email(research, SENDER_NAME, SENDER_ROLE,
                                    SERVICE_OFFERED, full_instruction, contact)


def check_all_replies() -> list:
    """Tüm 'sent' leadler için cevap var mı kontrol et. Cevap varsa 'replied' yap."""
    init_db()
    replied_companies = []
    with Session() as session:
        leads = session.query(Lead).filter(Lead.status == "sent").all()
        for lead in leads:
            if not lead.contact_email or not lead.draft_subject:
                continue
            try:
                if check_reply(lead.contact_email, lead.draft_subject):
                    update_status(lead.id, "replied")
                    replied_companies.append(lead.company_name)
                    print(f"  [cevap] {lead.company_name} → 'replied' olarak işaretlendi")
            except Exception as e:
                print(f"  [!] {lead.company_name} cevap kontrolü başarısız: {e}")
    return replied_companies


def get_due_for_followup() -> list:
    """Takip zamanı gelen leadleri döndür."""
    init_db()
    now = datetime.utcnow()
    due = []
    with Session() as session:
        leads = session.query(Lead).filter(Lead.status == "sent").all()
        for lead in leads:
            if not lead.sent_at or not lead.contact_email:
                continue
            fc = lead.follow_up_count or 0
            if fc >= 2:
                continue
            days_since = (now - lead.sent_at).days
            threshold = FOLLOW_UP_SCHEDULE[fc + 1]
            if days_since >= threshold:
                due.append((lead, fc + 1, days_since))
    return due


def run_follow_up_check():
    """Ana fonksiyon: cevapları kontrol et, follow-up zamanı gelenleri işle."""
    print("\n" + "=" * 60)
    print("FOLLOW-UP KONTROLÜ")
    print("=" * 60)

    # 1. Cevap kontrolü
    print("\n[1/2] Cevaplar kontrol ediliyor...")
    replied = check_all_replies()
    if replied:
        print(f"\n  Cevap gelenler: {', '.join(replied)}")
    else:
        print("  Yeni cevap yok.")

    # 2. Follow-up zamanı gelenler
    print("\n[2/2] Follow-up zamanı gelenler aranıyor...")
    due = get_due_for_followup()

    if not due:
        print("  Follow-up zamanı gelen lead yok.\n")
        return

    print(f"\n  {len(due)} lead için follow-up zamanı geldi.\n")

    for lead, follow_up_no, days_since in due:
        print(f"\n{'='*60}")
        print(f"  Şirket   : {lead.company_name}")
        print(f"  Kişi     : {lead.contact_name} <{lead.contact_email}>")
        print(f"  Pozisyon : {lead.contact_position or '—'}")
        print(f"  İlk email: {days_since} gün önce gönderildi")
        print(f"  Follow-up: #{follow_up_no}")
        print(f"{'='*60}")

        research = lead.research or {"company_name": lead.company_name, "domain": lead.company_domain}
        contact = {
            "first_name": lead.contact_name.split()[0] if lead.contact_name else "",
            "last_name": " ".join(lead.contact_name.split()[1:]) if lead.contact_name else "",
            "value": lead.contact_email,
            "position": lead.contact_position or ""
        }

        # Temel talimatla ilk taslağı oluştur
        base_instruction = _follow_up_base_instruction(follow_up_no, days_since)
        print("\nFollow-up taslağı hazırlanıyor...")
        draft = draft_email(research, SENDER_NAME, SENDER_ROLE, SERVICE_OFFERED, base_instruction, contact)

        # Onay menüsü (stiller + düzenleme + gönder/atla)
        draft, should_send = _approval_menu(draft, research, contact, follow_up_no, days_since)

        if should_send:
            success = send_email(lead.contact_email, draft["subject"], draft["body"])
            if success:
                increment_follow_up(lead.id)
        else:
            print(f"  Atlandı — {lead.company_name}")


if __name__ == "__main__":
    run_follow_up_check()
