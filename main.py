import sys
import os

sys.path.append(os.path.dirname(__file__))

from src.db.models import init_db


def main():
    init_db()

    while True:
        print("\n========== ProspectPilot ==========")
        print("[1] Yeni lead araştır ve email yaz")
        print("[2] CSV'den toplu işle (data/leads.csv)")
        print("[3] Kayıtlı lead'leri gör")
        print("[4] Follow-up kontrolü (cevap var mı? zamanı gelenler)")
        print("[5] Otomatik takip başlat (her gün 09:00)")
        print("[6] İstatistikler")
        print("[Q] Çık")

        choice = input("\nSeçim: ").strip().lower()

        if choice == "1":
            from src.pipeline.graph import run
            company = input("Şirket adı: ").strip()
            run(company)

        elif choice == "2":
            from src.pipeline.graph import run_batch
            run_batch()

        elif choice == "3":
            from src.db.viewer import menu
            menu()

        elif choice == "4":
            from src.tools.follow_up import run_follow_up_check
            run_follow_up_check()

        elif choice == "5":
            from src.scheduler import start_scheduler
            start_scheduler()

        elif choice == "6":
            from src.db.viewer import stats_menu
            stats_menu()

        elif choice == "q":
            break

        else:
            print("Geçersiz seçim.")


if __name__ == "__main__":
    main()
