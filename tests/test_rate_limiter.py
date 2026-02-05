import pytest
import asyncio
from secumator.core.rate_limiter import RateLimiter, RateLimitConfig, TokenBucket


@pytest.fixture
def bucket():
    return TokenBucket(rate=10.0, capacity=5)


@pytest.fixture
def limiter():
    config = RateLimitConfig(
        requests_per_second=10.0,
        burst_size=5,
        per_target_rps=2.0,
        per_target_burst=3,
        cooldown_on_error=1.0,
    )
    return RateLimiter(config)


@pytest.mark.asyncio
async def test_bucket_acquire(bucket):
    assert await bucket.acquire() is True
    assert bucket.tokens < 5


@pytest.mark.asyncio
async def test_bucket_exhaustion(bucket):
    for _ in range(5):
        assert await bucket.acquire() is True
    assert await bucket.acquire() is False


@pytest.mark.asyncio
async def test_bucket_refill(bucket):
    for _ in range(5):
        await bucket.acquire()
    await asyncio.sleep(0.2)
    assert await bucket.acquire() is True


@pytest.mark.asyncio
async def test_bucket_wait_and_acquire(bucket):
    for _ in range(5):
        await bucket.acquire()
    result = await bucket.wait_and_acquire(timeout=1.0)
    assert result is True


@pytest.mark.asyncio
async def test_bucket_get_status(bucket):
    status = bucket.get_status()
    assert "tokens" in status
    assert "capacity" in status
    assert "rate" in status


@pytest.mark.asyncio
async def test_limiter_acquire(limiter):
    assert await limiter.acquire("example.com") is True


@pytest.mark.asyncio
async def test_limiter_per_target_limit(limiter):
    target = "limited-target.com"
    for _ in range(3):
        assert await limiter.acquire(target) is True
    assert await limiter.acquire(target) is False


@pytest.mark.asyncio
async def test_limiter_different_targets(limiter):
    for i in range(5):
        assert await limiter.acquire(f"target{i}.com") is True


@pytest.mark.asyncio
async def test_limiter_cooldown_on_errors(limiter):
    target = "error-target.com"
    await limiter.report_error(target)
    await limiter.report_error(target)
    await limiter.report_error(target)

    assert await limiter.acquire(target) is False


@pytest.mark.asyncio
async def test_limiter_success_reduces_error_count(limiter):
    target = "success-target.com"
    await limiter.report_error(target)
    await limiter.report_success(target)
    await limiter.report_error(target)
    await limiter.report_error(target)

    assert await limiter.acquire(target) is True


@pytest.mark.asyncio
async def test_limiter_get_status(limiter):
    await limiter.acquire("status-target.com")
    status = limiter.get_status()

    assert "global" in status
    assert "targets" in status
    assert "status-target.com" in status["targets"]


@pytest.mark.asyncio
async def test_limiter_wait_and_acquire(limiter):
    target = "wait-target.com"
    for _ in range(3):
        await limiter.acquire(target)

    result = await limiter.wait_and_acquire(target, timeout=1.0)
    assert result is True


@pytest.mark.asyncio
async def test_limiter_wait_timeout():
    config = RateLimitConfig(
        requests_per_second=0.1,
        burst_size=1,
        per_target_rps=0.1,
        per_target_burst=1,
    )
    limiter = RateLimiter(config)
    target = "timeout-target.com"

    await limiter.acquire(target)
    result = await limiter.wait_and_acquire(target, timeout=0.1)
    assert result is False
