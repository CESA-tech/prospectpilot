import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import datetime
from src.db.models import init_db, Session, Lead
from src.db.crud import update_status, get_stats, reset_all_leads

init_db()


def _days_ago(dt) -> str:
    if not dt:
        return "—"
    diff = (datetime.utcnow() - dt).days
    if diff == 0:
        return "bugün"
    return f"{diff} gün önce"


def list_leads(status_filter=None):
    with Session() as session:
        query = session.query(Lead)
        if status_filter:
            query = query.filter(Lead.status == status_filter)
        leads = query.order_by(Lead.created_at.desc()).all()

        if not leads:
            print("Kayıt yok.")
            return

        print(f"\n{'ID':<5} {'Şirket':<22} {'Durum':<10} {'Gönderilme':<14} {'F/U':<6} {'Subject'}")
        print("-" * 100)
        for l in leads:
            sent = _days_ago(l.sent_at)
            fu = f"{l.follow_up_count or 0}/2" if l.status in ("sent", "replied") else "—"
            subject = (l.draft_subject or "")[:35]
            print(f"{l.id:<5} {l.company_name:<22} {l.status:<10} {sent:<14} {fu:<6} {subject}")
        print(f"\nToplam: {len(leads)} lead")
        print("F/U = Follow-up sayısı (kaç takip emaili gönderildi / maksimum 2)")


def show_lead(lead_id: int):
    with Session() as session:
        lead = session.get(Lead, lead_id)
        if not lead:
            print(f"ID {lead_id} bulunamadı.")
            return

        print(f"\n{'='*60}")
        print(f"Şirket     : {lead.company_name}")
        print(f"Domain     : {lead.company_domain or '—'}")
        print(f"Durum      : {lead.status}")
        print(f"Oluşturulma: {lead.created_at.strftime('%Y-%m-%d %H:%M') if lead.created_at else '—'}")
        if lead.sent_at:
            print(f"Gönderilme : {lead.sent_at.strftime('%Y-%m-%d %H:%M')} ({_days_ago(lead.sent_at)})")
            print(f"Follow-up  : {lead.follow_up_count or 0}/2")
        if lead.contact_email:
            print(f"\nAlıcı      : {lead.contact_name} — {lead.contact_position or '—'}")
            print(f"Email      : {lead.contact_email}")
        print(f"\nSUBJECT:\n{lead.draft_subject or '—'}")
        print(f"\nBODY:\n{lead.draft_body or '—'}")
        if lead.research:
            print(f"\nARAŞTIRMA ÖZETİ:\n{lead.research.get('summary', '—')}")
        print("=" * 60)

        _lead_actions(lead)


def _lead_actions(lead):
    """Lead detay sayfasında yapılabilecek işlemler."""
    options = []

    if lead.status == "draft":
        options.append(("[D] Devam et (gönder / düzenle)", "d"))
    if lead.status in ("sent",):
        options.append(("[R] Replied olarak işaretle", "r"))
    options.append(("[S] Sil", "s"))
    options.append(("[Q] Geri dön", "q"))

    for label, _ in options:
        print(f"  {label}")

    choice = input("\nSeçim: ").strip().lower()

    if choice == "d" and lead.status == "draft":
        from src.pipeline.graph import resume_lead
        resume_lead(lead.id)

    elif choice == "r" and lead.status == "sent":
        confirm = input("Bu lead'i 'replied' olarak işaretle? (e/h): ").strip().lower()
        if confirm == "e":
            update_status(lead.id, "replied")
            print(f"  Lead #{lead.id} → replied olarak işaretlendi.")

    elif choice == "s":
        confirm = input(f"'{lead.company_name}' silinsin mi? Bu işlem geri alınamaz. (e/h): ").strip().lower()
        if confirm == "e":
            with Session() as session:
                l = session.get(Lead, lead.id)
                if l:
                    session.delete(l)
                    session.commit()
                    print(f"  Lead #{lead.id} silindi.")


def stats_menu():
    stats = get_stats()
    total = stats["total"]
    sent = stats["sent"]

    print("\n===== İSTATİSTİKLER =====\n")
    print(f"  Toplam lead    : {total}")
    print(f"  Taslak         : {stats['draft']}")
    print(f"  Gönderildi     : {sent}")
    print(f"  Cevap geldi    : {stats['replied']}")

    if sent > 0:
        oran = round((stats["replied"] / sent) * 100)
        print(f"\n  Dönüşüm oranı  : %{oran}  (cevap / gönderilen)")

    print(f"\n  Follow-up bekleyen  : {stats['fu_pending']}")
    print(f"  Follow-up tamamlanan: {stats['fu_done']}")

    print("\n  [R] Tüm leadleri sıfırla")
    print("  [Q] Geri dön")

    choice = input("\nSeçim: ").strip().lower()

    if choice == "r":
        if total == 0:
            print("Silinecek lead yok.")
            return
        print(f"\n  {total} lead silinecek. Bu işlem geri alınamaz.")
        onay = input("  Onaylamak için 'SIFIRLA' yaz: ").strip()
        if onay == "SIFIRLA":
            reset_all_leads()
            print("  Tüm leadler silindi.")
        else:
            print("  İptal edildi.")


def menu():
    while True:
        print("\n--- ProspectPilot DB Viewer ---")
        print("[1] Tüm lead'leri listele")
        print("[2] Statüye göre filtrele (draft / sent / replied)")
        print("[3] Lead seç — detay gör, işlem yap")
        print("[Q] Çık")

        choice = input("\nSeçim: ").strip().lower()

        if choice == "1":
            list_leads()
        elif choice == "2":
            status = input("Statü (draft / sent / replied): ").strip()
            list_leads(status)
        elif choice == "3":
            lead_id = input("Lead ID: ").strip()
            if lead_id.isdigit():
                show_lead(int(lead_id))
            else:
                print("Geçersiz ID.")
        elif choice == "q":
            break
        else:
            print("Geçersiz seçim.")


if __name__ == "__main__":
    menu()
