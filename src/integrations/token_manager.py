"""
Automatic Shopify access token manager.

Client Credentials Grant tokens expire after ~24h. Instead of requiring a
human to re-run get_shopify_token.py and paste the result into .env every
day, this module fetches the token on first use, caches it in memory with
its expiry time, and transparently refreshes it before it expires (or if
Shopify rejects it with a 401).

Only SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, and SHOPIFY_SHOP_DOMAIN need
to live in .env — SHOPIFY_ACCESS_TOKEN is no longer needed there at all.
"""

import os
import time
import threading
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")
SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN")

# Refresh a bit before actual expiry so a request never gets caught out
# mid-flight by an already-dead token.
_SAFETY_MARGIN_SECONDS = 300  # 5 minutes

_lock = threading.Lock()
_cached_token: str | None = None
_expires_at: float = 0.0  # unix timestamp


def _request_new_token() -> tuple[str, int]:
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

    return data["access_token"], data.get("expires_in", 82800)  # default ~23h


def get_valid_token(force_refresh: bool = False) -> str:
    """
    Return a currently-valid access token, fetching or refreshing it
    automatically as needed. Thread-safe.

    force_refresh: pass True after a 401 to bypass the cache and get a
    brand new token immediately (handles the case where Shopify revoked
    or expired the token earlier than expected).
    """
    global _cached_token, _expires_at

    with _lock:
        now = time.time()
        if (
            force_refresh
            or _cached_token is None
            or now >= (_expires_at - _SAFETY_MARGIN_SECONDS)
        ):
            token, expires_in = _request_new_token()
            _cached_token = token
            _expires_at = now + expires_in
            print(
                f"[token_manager] Refreshed Shopify access token "
                f"(valid ~{expires_in // 3600}h)."
            )

        return _cached_token


if __name__ == "__main__":
    # Manual check: run this file directly to confirm token fetching works.
    tok = get_valid_token()
    print(f"Token acquired, starts with: {tok[:12]}...")
