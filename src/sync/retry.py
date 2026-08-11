"""
Retry logic dengan exponential backoff.

Dipakai untuk membungkus pemanggilan API yang mungkin gagal sementara
(network error, rate limit, server down) — dicoba ulang beberapa kali
dengan jeda yang makin lama, bukan langsung menyerah.
"""

import time
import functools
from requests.exceptions import RequestException


def retry_with_backoff(max_attempts: int = 4, base_delay: float = 1.0):
    """
    Decorator: bungkus fungsi supaya otomatis dicoba ulang kalau gagal.

    max_attempts : berapa kali total percobaan (termasuk yang pertama)
    base_delay   : jeda awal dalam detik, dilipatgandakan tiap percobaan gagal
                   (1s -> 2s -> 4s -> 8s, dst)

    Contoh pakai:
        @retry_with_backoff(max_attempts=4, base_delay=1.0)
        def fetch_orders():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except RequestException as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    delay = base_delay * (2 ** (attempt - 1))
                    print(
                        f"[retry] Percobaan {attempt}/{max_attempts} gagal "
                        f"({e}). Coba lagi dalam {delay:.0f} detik..."
                    )
                    time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator
