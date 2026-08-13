"""
Retry logic with exponential backoff.

Wraps API calls that may fail transiently (network errors, rate limits,
server downtime) so they're retried with increasing delay instead of
failing immediately.
"""

import time
import functools
from requests.exceptions import RequestException


def retry_with_backoff(max_attempts: int = 4, base_delay: float = 1.0):
    """
    Decorator: wrap a function so it's automatically retried on failure.

    max_attempts : total number of attempts (including the first)
    base_delay   : initial delay in seconds, doubled on each failed attempt
                   (1s -> 2s -> 4s -> 8s, ...)

    Usage:
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
                        f"[retry] Attempt {attempt}/{max_attempts} failed "
                        f"({e}). Retrying in {delay:.0f}s..."
                    )
                    time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator
