import asyncio
import time
from collections import defaultdict
from typing import Dict, Tuple
from src.config import settings


class RateLimiter:
    """Simple rate limiter for LUMA API requests."""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked_until: Dict[str, float] = {}

    def _clean_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests outside the current window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff_time
        ]

    def _is_blocked(self, key: str) -> bool:
        """Check if a key is currently blocked."""
        current_time = time.time()
        if key in self.blocked_until:
            if current_time < self.blocked_until[key]:
                return True
            else:
                del self.blocked_until[key]
        return False

    def can_make_request(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if a request can be made for the given key."""
        if self._is_blocked(key):
            return False

        self._clean_old_requests(key, window_seconds)
        return len(self.requests[key]) < max_requests

    def record_request(self, key: str) -> None:
        """Record a request for rate limiting."""
        current_time = time.time()
        self.requests[key].append(current_time)

    def block_key(self, key: str, duration_seconds: int) -> None:
        """Block a key for the specified duration."""
        self.blocked_until[key] = time.time() + duration_seconds

    async def wait_if_needed(self, key: str, max_requests: int, window_seconds: int) -> None:
        """Wait until a request can be made, with exponential backoff if blocked."""
        wait_count = 0
        max_total_wait = 600  # Max 10 minutes total wait time
        while not self.can_make_request(key, max_requests, window_seconds):
            if wait_count * 1 > max_total_wait:
                raise Exception(f"Rate limiter timeout: waited too long for {key}")

            if self._is_blocked(key):
                # Exponential backoff for blocked keys
                wait_time = min(settings.retry_backoff_factor ** len(self.requests[key]), 300)  # Max 5 minutes
                await asyncio.sleep(wait_time)
            else:
                # Wait for window to reset
                await asyncio.sleep(1)
            wait_count += 1


# Global rate limiter instances
get_limiter = RateLimiter()
post_limiter = RateLimiter()


async def rate_limit_request(endpoint: str, method: str = "GET") -> None:
    """Apply rate limiting to a request."""
    if method.upper() == "GET":
        await get_limiter.wait_if_needed(
            endpoint,
            settings.rate_limit_get_requests,
            settings.rate_limit_window_seconds
        )
        get_limiter.record_request(endpoint)
    else:
        await post_limiter.wait_if_needed(
            endpoint,
            settings.rate_limit_post_requests,
            settings.rate_limit_window_seconds
        )
        post_limiter.record_request(endpoint)