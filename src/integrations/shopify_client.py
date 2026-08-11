"""
Client untuk mengambil data order dari Shopify Admin API.
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
API_VERSION = "2026-07"  # samakan dengan versi yang dipilih waktu bikin app


@retry_with_backoff(max_attempts=4, base_delay=1.0)
def fetch_orders(limit: int = 50) -> list[dict]:
    """
    Ambil daftar order terbaru dari toko Shopify.

    Return: list of dict, masing-masing berisi data 1 order
    (sudah disederhanakan agar cocok dengan format yang dibutuhkan validator).
    """
    if not SHOP_DOMAIN or not ACCESS_TOKEN:
        raise ValueError(
            "SHOPIFY_SHOP_DOMAIN dan SHOPIFY_ACCESS_TOKEN harus terisi di .env"
        )

    url = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}/orders.json"

    response = requests.get(
        url,
        headers={"X-Shopify-Access-Token": ACCESS_TOKEN},
        params={"limit": limit, "status": "any"},
    )
    response.raise_for_status()

    raw_orders = response.json().get("orders", [])

    # Ubah format Shopify (kompleks) jadi format sederhana yang dipakai validator kita
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
                "raw_payload": order,  # simpan data asli lengkap, buat jaga-jaga
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
    # Uji coba manual: jalankan langsung file ini untuk lihat hasilnya
    orders = fetch_orders()
    print(f"Berhasil ambil {len(orders)} order:\n")
    for o in orders:
        print(o)
