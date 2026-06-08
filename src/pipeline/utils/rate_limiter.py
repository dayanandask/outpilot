import asyncio
import time
from typing import Dict


class RateLimiter:
    """A token-bucket rate limiter for outgoing API requests."""

    def __init__(self, requests_per_minute: int):
        self.rate = float(requests_per_minute)
        self.capacity = float(requests_per_minute)
        self.tokens = float(requests_per_minute)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill

                # Refill tokens based on elapsed time
                refill_amount = elapsed * (self.rate / 60.0)
                if refill_amount > 0:
                    self.tokens = min(self.capacity, self.tokens + refill_amount)
                    self.last_refill = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

            # Wait a bit before checking again
            await asyncio.sleep(0.1)


# Global rate limiters instance dictionary
_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(service_name: str, requests_per_minute: int) -> RateLimiter:
    """Returns a singleton RateLimiter for a given service."""
    if service_name not in _limiters:
        _limiters[service_name] = RateLimiter(requests_per_minute)
    return _limiters[service_name]
