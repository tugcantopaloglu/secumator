import pytest
from datetime import datetime, timezone, timedelta
from secumator.core.queue import ScanQueue, Priority


@pytest.fixture
def queue():
    return ScanQueue(max_concurrent=2, rate_limit_per_minute=10)


@pytest.mark.asyncio
async def test_enqueue_scan(queue):
    queue_id = await queue.enqueue(scan_id=1, priority=Priority.NORMAL)
    assert queue_id is not None
    assert len(queue._queue) == 1


@pytest.mark.asyncio
async def test_priority_ordering(queue):
    await queue.enqueue(scan_id=1, priority=Priority.LOW)
    await queue.enqueue(scan_id=2, priority=Priority.CRITICAL)
    await queue.enqueue(scan_id=3, priority=Priority.HIGH)

    queued = await queue.dequeue()
    assert queued is not None
    assert queued.scan_id == 2

    queued = await queue.dequeue()
    assert queued.scan_id == 3


@pytest.mark.asyncio
async def test_scheduled_scan(queue):
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    await queue.enqueue(scan_id=1, scheduled_at=future_time)

    queued = await queue.dequeue()
    assert queued is None


@pytest.mark.asyncio
async def test_max_concurrent(queue):
    queue_id1 = await queue.enqueue(scan_id=1)
    await queue.enqueue(scan_id=2)
    await queue.enqueue(scan_id=3)

    await queue.dequeue()
    await queue.dequeue()
    queued = await queue.dequeue()
    assert queued is None

    await queue.complete(queue_id1)
    queued = await queue.dequeue()
    assert queued is not None
    assert queued.scan_id == 3


@pytest.mark.asyncio
async def test_cancel_queued(queue):
    queue_id = await queue.enqueue(scan_id=1)
    success = await queue.cancel(queue_id)
    assert success is True
    assert len(queue._queue) == 0


@pytest.mark.asyncio
async def test_retry_on_failure(queue):
    queue_id = await queue.enqueue(scan_id=1)
    await queue.dequeue()
    await queue.complete(queue_id, success=False, error="Test error")

    assert len(queue._queue) == 1
    assert queue._queue[0].retries == 1


@pytest.mark.asyncio
async def test_get_status(queue):
    await queue.enqueue(scan_id=1)
    await queue.enqueue(scan_id=2)
    await queue.dequeue()

    status = queue.get_status()
    assert status["queued"] == 1
    assert status["running"] == 1


@pytest.mark.asyncio
async def test_get_queue_items(queue):
    await queue.enqueue(scan_id=1, priority=Priority.HIGH)
    await queue.enqueue(scan_id=2, priority=Priority.LOW)

    items = queue.get_queue_items()
    assert len(items) == 2
    assert items[0]["scan_id"] == 1
    assert items[0]["priority"] == "HIGH"
