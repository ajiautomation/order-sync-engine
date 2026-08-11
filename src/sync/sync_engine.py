"""
Sync Engine — inti dari proyek ini.

Alur:
1. Ambil order dari Shopify
2. Validasi tiap order
3. Valid -> simpan ke tabel `orders` (skip kalau sudah ada, biar idempotent)
4. Invalid -> simpan ke tabel `quarantine` beserta alasannya
5. Catat ringkasan proses ke tabel `sync_log`

Jalankan: python src/sync/sync_engine.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import datetime, timezone

from src.db.connection import get_session
from src.db.models import Order, Quarantine, SyncLog
from src.integrations.shopify_client import fetch_orders
from src.validation.order_validator import validate_order


def run_sync():
    session = get_session()

    orders_fetched = 0
    orders_synced = 0
    orders_quarantined = 0
    status = "success"
    error_message = None

    try:
        orders = fetch_orders()
        orders_fetched = len(orders)

        for order_data in orders:
            result = validate_order(order_data)

            if result.is_valid:
                _save_valid_order(session, order_data)
                orders_synced += 1
            else:
                _save_quarantined_order(session, order_data, result.reason)
                orders_quarantined += 1

        session.commit()

    except Exception as e:
        session.rollback()
        status = "failed"
        error_message = str(e)

    finally:
        log = SyncLog(
            run_at=datetime.now(timezone.utc),
            orders_fetched=orders_fetched,
            orders_synced=orders_synced,
            orders_quarantined=orders_quarantined,
            status=status,
            error_message=error_message,
        )
        session.add(log)
        session.commit()
        session.close()

    return {
        "orders_fetched": orders_fetched,
        "orders_synced": orders_synced,
        "orders_quarantined": orders_quarantined,
        "status": status,
        "error_message": error_message,
    }


def _save_valid_order(session, order_data: dict):
    """
    Simpan order valid ke tabel `orders`.
    Idempotent: kalau shopify_order_id sudah ada, update saja, jangan bikin baris baru.
    """
    existing = (
        session.query(Order)
        .filter_by(shopify_order_id=order_data["shopify_order_id"])
        .first()
    )

    if existing:
        existing.customer_name = order_data["customer_name"]
        existing.sku = order_data["sku"]
        existing.quantity = order_data["quantity"]
        existing.price = order_data["price"]
        existing.raw_payload = order_data.get("raw_payload")
        existing.updated_at = datetime.now(timezone.utc)
    else:
        new_order = Order(
            shopify_order_id=order_data["shopify_order_id"],
            customer_name=order_data["customer_name"],
            sku=order_data["sku"],
            quantity=order_data["quantity"],
            price=order_data["price"],
            raw_payload=order_data.get("raw_payload"),
            status="synced",
        )
        session.add(new_order)


def _save_quarantined_order(session, order_data: dict, reason: str):
    """Simpan order yang gagal validasi ke tabel `quarantine`."""
    quarantine_entry = Quarantine(
        shopify_order_id=order_data.get("shopify_order_id", "unknown"),
        raw_payload=order_data.get("raw_payload"),
        failure_reason=reason,
    )
    session.add(quarantine_entry)


if __name__ == "__main__":
    result = run_sync()
    print("\nSync selesai!\n")
    print(f"Status              : {result['status']}")
    print(f"Order diambil       : {result['orders_fetched']}")
    print(f"Order berhasil sync : {result['orders_synced']}")
    print(f"Order di-quarantine : {result['orders_quarantined']}")
    if result["error_message"]:
        print(f"Error               : {result['error_message']}")
