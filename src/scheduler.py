"""
Scheduler — menjalankan sync_engine secara otomatis berkala.

Ini yang membuat proyek "hidup" tanpa perlu dijalankan manual terus-menerus.
Kalau satu kali sync gagal (misal internet mati), scheduler akan tetap
mencoba lagi di jadwal berikutnya — bukan menyerah selamanya.

Jalankan: python src/scheduler.py
Hentikan dengan: Ctrl+C
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
    print(f"\n[{timestamp}] Menjalankan sync terjadwal...")

    result = run_sync()

    print(
        f"[{timestamp}] Selesai — status: {result['status']}, "
        f"diambil: {result['orders_fetched']}, "
        f"sync: {result['orders_synced']}, "
        f"quarantine: {result['orders_quarantined']}"
    )

    if result["status"] == "failed":
        print(f"[{timestamp}] Sync gagal kali ini, akan dicoba lagi di jadwal berikutnya.")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(
        scheduled_job,
        "interval",
        minutes=SYNC_INTERVAL_MINUTES,
        next_run_time=datetime.now(),  # jalankan sekali langsung saat start
    )

    print(f"Scheduler aktif — sync akan berjalan setiap {SYNC_INTERVAL_MINUTES} menit.")
    print("Tekan Ctrl+C untuk berhenti.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler dihentikan.")
