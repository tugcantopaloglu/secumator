import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from secumator.core import get_logger

logger = get_logger("rate_limiter")


@dataclass
class RateLimitConfig:
    requests_per_second: float = 10.0
    burst_size: int = 20
    per_target_rps: float = 2.0
    per_target_burst: int = 5
    cooldown_on_error: float = 30.0


class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_and_acquire(self, tokens: int = 1, timeout: float = 60.0) -> bool:
        start = time.monotonic()
        while True:
            if await self.acquire(tokens):
                return True
            if time.monotonic() - start > timeout:
                return False
            wait_time = (tokens - self.tokens) / self.rate
            await asyncio.sleep(min(wait_time, 1.0))

    def get_status(self) -> dict[str, Any]:
        return {
            "tokens": round(self.tokens, 2),
            "capacity": self.capacity,
            "rate": self.rate,
        }


class RateLimiter:
    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._global_bucket = TokenBucket(
            self.config.requests_per_second, self.config.burst_size
        )
        self._target_buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.config.per_target_rps, self.config.per_target_burst)
        )
        self._cooldowns: dict[str, float] = {}
        self._request_counts: dict[str, int] = defaultdict(int)
        self._error_counts: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def acquire(self, target: str) -> bool:
        async with self._lock:
            if target in self._cooldowns:
                if time.monotonic() < self._cooldowns[target]:
                    logger.warning("target_in_cooldown", target=target)
                    return False
                del self._cooldowns[target]

        if not await self._global_bucket.acquire():
            logger.debug("global_rate_limit_hit")
            return False

        if not await self._target_buckets[target].acquire():
            logger.debug("target_rate_limit_hit", target=target)
            return False

        async with self._lock:
            self._request_counts[target] += 1

        return True

    async def wait_and_acquire(self, target: str, timeout: float = 60.0) -> bool:
        start = time.monotonic()
        while True:
            if await self.acquire(target):
                return True
            if time.monotonic() - start > timeout:
                return False
            await asyncio.sleep(0.1)

    async def report_error(self, target: str):
        async with self._lock:
            self._error_counts[target] += 1
            if self._error_counts[target] >= 3:
                self._cooldowns[target] = time.monotonic() + self.config.cooldown_on_error
                self._error_counts[target] = 0
                logger.warning(
                    "target_cooldown_applied",
                    target=target,
                    duration=self.config.cooldown_on_error,
                )

    async def report_success(self, target: str):
        async with self._lock:
            self._error_counts[target] = max(0, self._error_counts[target] - 1)

    def get_status(self) -> dict[str, Any]:
        return {
            "global": self._global_bucket.get_status(),
            "targets": {
                target: {
                    "bucket": bucket.get_status(),
                    "requests": self._request_counts.get(target, 0),
                    "errors": self._error_counts.get(target, 0),
                    "in_cooldown": target in self._cooldowns,
                }
                for target, bucket in list(self._target_buckets.items())[:20]
            },
        }


rate_limiter = RateLimiter()
