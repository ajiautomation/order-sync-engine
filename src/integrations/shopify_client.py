"""
Client for fetching order data from the Shopify Admin API.
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.sync.retry import retry_with_backoff

load_dotenv()

SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2026-07"  # keep in sync with the version chosen when the app was created


@retry_with_backoff(max_attempts=4, base_delay=1.0)
def fetch_orders(limit: int = 50) -> list[dict]:
    """
    Fetch the most recent orders from the Shopify store.

    Returns: a list of dicts, one per order (already flattened to the
    simplified format expected by the validator).
    """
    if not SHOP_DOMAIN or not ACCESS_TOKEN:
        raise ValueError(
            "SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN must be set in .env"
        )

    url = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}/orders.json"

    response = requests.get(
        url,
        headers={"X-Shopify-Access-Token": ACCESS_TOKEN},
        params={"limit": limit, "status": "any"},
    )
    response.raise_for_status()

    raw_orders = response.json().get("orders", [])

    # Flatten Shopify's nested order format into the simplified shape our validator expects
    simplified_orders = []
    for order in raw_orders:
        line_items = order.get("line_items", [])
        first_item = line_items[0] if line_items else {}

        simplified_orders.append(
            {
                "shopify_order_id": str(order.get("id")),
                "customer_name": _get_customer_name(order),
                "sku": first_item.get("sku") or first_item.get("title", ""),
                "quantity": first_item.get("quantity", 0),
                "price": float(order.get("total_price", 0)),
                "raw_payload": order,  # keep the full original payload for reference
            }
        )

    return simplified_orders


def _get_customer_name(order: dict) -> str:
    customer = order.get("customer")
    if not customer:
        return ""
    first = customer.get("first_name", "") or ""
    last = customer.get("last_name", "") or ""
    return f"{first} {last}".strip()


if __name__ == "__main__":
    # Manual smoke test: run this file directly to see the result
    orders = fetch_orders()
    print(f"Fetched {len(orders)} orders:\n")
    for o in orders:
        print(o)
