"""
Client for fetching order data from the Shopify Admin API.
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.sync.retry import retry_with_backoff
from src.integrations.token_manager import get_valid_token

load_dotenv()

SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN")
API_VERSION = "2026-07"  # keep in sync with the version chosen when the app was created


@retry_with_backoff(max_attempts=4, base_delay=1.0)
def fetch_orders(limit: int = 50) -> list[dict]:
    """
    Fetch the most recent orders from the Shopify store.

    The access token is obtained automatically (and refreshed automatically
    when close to expiry, or immediately if Shopify returns 401) — no
    manual token handling required.

    Returns: a list of dicts, one per order (already flattened to the
    simplified format expected by the validator).
    """
    if not SHOP_DOMAIN:
        raise ValueError("SHOPIFY_SHOP_DOMAIN must be set in .env")

    url = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}/orders.json"

    token = get_valid_token()
    response = requests.get(
        url,
        headers={"X-Shopify-Access-Token": token},
        params={"limit": limit, "status": "any"},
    )

    if response.status_code == 401:
        # Token was rejected earlier than expected (revoked, clock drift,
        # etc.) — force a fresh one and retry once before giving up.
        token = get_valid_token(force_refresh=True)
        response = requests.get(
            url,
            headers={"X-Shopify-Access-Token": token},
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
