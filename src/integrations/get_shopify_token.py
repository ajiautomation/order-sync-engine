"""
Script sekali-jalan untuk menukar Client ID + Secret menjadi Admin API access token.

Shopify (sejak awal 2026) tidak lagi menampilkan access token langsung di halaman web.
Token harus diminta lewat request terprogram (Client Credentials Grant).

Jalankan: python src/integrations/get_shopify_token.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")
SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN")


def get_access_token():
    if not all([CLIENT_ID, CLIENT_SECRET, SHOP_DOMAIN]):
        raise ValueError(
            "Pastikan SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, dan "
            "SHOPIFY_SHOP_DOMAIN sudah terisi di file .env"
        )

    url = f"https://{SHOP_DOMAIN}/admin/oauth/access_token"

    response = requests.post(
        url,
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        headers={"Content-Type": "application/json"},
    )

    response.raise_for_status()
    data = response.json()

    return data["access_token"], data.get("expires_in")


if __name__ == "__main__":
    token, expires_in = get_access_token()
    print("\nBerhasil dapat access token!\n")
    print(f"Access token : {token}")
    print(f"Berlaku      : {expires_in} detik (~{expires_in // 3600} jam)")
    print("\nTambahkan baris ini ke file .env kamu:")
    print(f"SHOPIFY_ACCESS_TOKEN={token}")
