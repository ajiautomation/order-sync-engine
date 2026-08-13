"""
Scheduler — runs sync_engine automatically on a recurring interval.

This is what makes the project run unattended instead of needing a
manual trigger every time. If one sync run fails (e.g. the network is
down), the scheduler keeps trying on the next cycle instead of giving
up permanently.

Run: python -m src.scheduler
Stop with: Ctrl+C
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from src.sync.sync_engine import run_sync

load_dotenv()

SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", 15))


def scheduled_job():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"\n[{timestamp}] Running scheduled sync...")

    result = run_sync()

    print(
        f"[{timestamp}] Done — status: {result['status']}, "
        f"fetched: {result['orders_fetched']}, "
        f"synced: {result['orders_synced']}, "
        f"quarantined: {result['orders_quarantined']}"
    )

    if result["status"] == "failed":
        print(f"[{timestamp}] This run failed — will retry on the next scheduled cycle.")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(
        scheduled_job,
        "interval",
        minutes=SYNC_INTERVAL_MINUTES,
        next_run_time=datetime.now(),  # also run once immediately on start
    )

    print(f"Scheduler active — sync will run every {SYNC_INTERVAL_MINUTES} minutes.")
    print("Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped.")
