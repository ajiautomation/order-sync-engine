"""
Sync Engine — the core of this project.

Flow:
1. Fetch orders from Shopify
2. Validate each order
3. Valid   -> upsert into the `orders` table (idempotent, no duplicates on re-run)
4. Invalid -> save to the `quarantine` table with the failure reason
5. Record a summary of the run in the `sync_log` table

Run: python -m src.sync.sync_engine
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
    Save a valid order to the `orders` table.
    Idempotent: if shopify_order_id already exists, update it instead of
    inserting a new row.
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
    """Save an order that failed validation to the `quarantine` table."""
    quarantine_entry = Quarantine(
        shopify_order_id=order_data.get("shopify_order_id", "unknown"),
        raw_payload=order_data.get("raw_payload"),
        failure_reason=reason,
    )
    session.add(quarantine_entry)


if __name__ == "__main__":
    result = run_sync()
    print("\nSync complete!\n")
    print(f"Status              : {result['status']}")
    print(f"Orders fetched      : {result['orders_fetched']}")
    print(f"Orders synced       : {result['orders_synced']}")
    print(f"Orders quarantined  : {result['orders_quarantined']}")
    if result["error_message"]:
        print(f"Error               : {result['error_message']}")
