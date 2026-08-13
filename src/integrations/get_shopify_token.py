"""
One-off script to exchange a Client ID + Secret for an Admin API access token.

As of early 2026, Shopify no longer displays the access token directly in
the admin UI — it must be requested programmatically via Client Credentials
Grant.

Run: python -m src.integrations.get_shopify_token
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
            "Make sure SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, and "
            "SHOPIFY_SHOP_DOMAIN are set in your .env file"
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
    print("\nAccess token retrieved successfully!\n")
    print(f"Access token : {token}")
    print(f"Expires in   : {expires_in} seconds (~{expires_in // 3600} hours)")
    print("\nAdd this line to your .env file:")
    print(f"SHOPIFY_ACCESS_TOKEN={token}")
