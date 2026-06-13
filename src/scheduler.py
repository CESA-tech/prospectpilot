import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from apscheduler.schedulers.blocking import BlockingScheduler
from src.tools.follow_up import run_follow_up_check

CHECK_HOUR = 9    # Her gün saat kaçta çalışsın
CHECK_MINUTE = 0


def start_scheduler():
    scheduler = BlockingScheduler(timezone="Europe/Istanbul")
    scheduler.add_job(
        run_follow_up_check,
        trigger="cron",
        hour=CHECK_HOUR,
        minute=CHECK_MINUTE,
        id="daily_followup_check"
    )

    print(f"Scheduler başlatıldı.")
    print(f"Follow-up kontrolü her gün {CHECK_HOUR:02d}:{CHECK_MINUTE:02d}'de çalışacak.")
    print("Durdurmak için Ctrl+C\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler durduruldu.")


if __name__ == "__main__":
    start_scheduler()
