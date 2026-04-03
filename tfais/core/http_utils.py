"""Shared HTTP utilities — thin helpers, not a class."""
import asyncio
import logging
import time

log = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
}


def retry_request(fn, max_retries=3, backoff=2):
    """Retry a callable with exponential backoff. Returns the result on success."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            wait = backoff ** attempt
            log.warning(f"Retry {attempt + 1}/{max_retries} after {wait}s: {exc}")
            time.sleep(wait)


def rate_limit(seconds=2):
    """Polite delay between requests."""
    time.sleep(seconds)


async def rate_limit_async(seconds: float = 2.0) -> None:
    """Non-blocking polite delay between async requests."""
    await asyncio.sleep(seconds)


async def retry_request_async(async_fn, max_retries=3, backoff=2):
    """
    Retry an async callable with exponential backoff.

    async_fn must be a zero-argument callable that returns a fresh coroutine
    each time it is called (e.g. ``lambda: session.get(url)``).
    A pre-created coroutine object cannot be used because coroutines can only
    be awaited once.
    """
    for attempt in range(max_retries):
        try:
            return await async_fn()
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            wait = backoff ** attempt
            log.warning(f"Async retry {attempt + 1}/{max_retries} after {wait}s: {exc}")
            await asyncio.sleep(wait)
