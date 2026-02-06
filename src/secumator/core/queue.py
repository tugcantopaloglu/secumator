import asyncio
import heapq
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Callable, Coroutine
from uuid import uuid4
from secumator.core import get_logger


class Priority(IntEnum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass(order=True)
class QueuedScan:
    priority: int
    scheduled_at: datetime = field(compare=False)
    scan_id: int = field(compare=False)
    queue_id: str = field(compare=False, default_factory=lambda: str(uuid4()))
    options: dict[str, Any] = field(compare=False, default_factory=dict)
    created_at: datetime = field(compare=False, default_factory=lambda: datetime.now(timezone.utc))
    retries: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)


class ScanQueue:
    def __init__(self, max_concurrent: int = 5, rate_limit_per_minute: int = 30):
        self.logger = get_logger("scan_queue")
        self._queue: list[QueuedScan] = []
        self._running: dict[str, QueuedScan] = {}
        self._completed: list[str] = []
        self._failed: list[tuple[str, str]] = []
        self.max_concurrent = max_concurrent
        self.rate_limit_per_minute = rate_limit_per_minute
        self._execution_times: list[datetime] = []
        self._lock = asyncio.Lock()
        self._process_task: asyncio.Task | None = None
        self._scan_callback: Callable[[int], Coroutine[Any, Any, bool]] | None = None
        self._running_flag = False

    def set_scan_callback(self, callback: Callable[[int], Coroutine[Any, Any, bool]]):
        self._scan_callback = callback

    async def enqueue(
        self,
        scan_id: int,
        priority: Priority = Priority.NORMAL,
        scheduled_at: datetime | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        async with self._lock:
            queued = QueuedScan(
                priority=priority.value,
                scheduled_at=scheduled_at or datetime.now(timezone.utc),
                scan_id=scan_id,
                options=options or {},
            )
            heapq.heappush(self._queue, queued)
            self.logger.info(
                "scan_enqueued",
                queue_id=queued.queue_id,
                scan_id=scan_id,
                priority=priority.name,
                scheduled_at=queued.scheduled_at.isoformat(),
            )
            return queued.queue_id

    async def dequeue(self) -> QueuedScan | None:
        async with self._lock:
            now = datetime.now(timezone.utc)
            self._execution_times = [t for t in self._execution_times if (now - t).total_seconds() < 60]

            if len(self._execution_times) >= self.rate_limit_per_minute:
                return None

            if len(self._running) >= self.max_concurrent:
                return None

            if not self._queue:
                return None

            queued = self._queue[0]
            if queued.scheduled_at > now:
                return None

            heapq.heappop(self._queue)
            self._running[queued.queue_id] = queued
            self._execution_times.append(now)
            return queued

    async def complete(self, queue_id: str, success: bool = True, error: str | None = None):
        async with self._lock:
            if queue_id not in self._running:
                return

            queued = self._running.pop(queue_id)
            if success:
                self._completed.append(queue_id)
                self.logger.info("scan_completed", queue_id=queue_id, scan_id=queued.scan_id)
            else:
                if queued.retries < queued.max_retries:
                    queued.retries += 1
                    heapq.heappush(self._queue, queued)
                    self.logger.warning(
                        "scan_retrying",
                        queue_id=queue_id,
                        scan_id=queued.scan_id,
                        retry=queued.retries,
                    )
                else:
                    self._failed.append((queue_id, error or "Max retries exceeded"))
                    self.logger.error(
                        "scan_failed_permanently",
                        queue_id=queue_id,
                        scan_id=queued.scan_id,
                        error=error,
                    )

    async def cancel(self, queue_id: str) -> bool:
        async with self._lock:
            for i, queued in enumerate(self._queue):
                if queued.queue_id == queue_id:
                    self._queue.pop(i)
                    heapq.heapify(self._queue)
                    self.logger.info("scan_cancelled", queue_id=queue_id)
                    return True
            return False

    def get_status(self) -> dict[str, Any]:
        return {
            "queued": len(self._queue),
            "running": len(self._running),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "rate_limit_remaining": max(0, self.rate_limit_per_minute - len(self._execution_times)),
            "is_processing": self._running_flag,
        }

    def get_queue_items(self) -> list[dict[str, Any]]:
        return [
            {
                "queue_id": q.queue_id,
                "scan_id": q.scan_id,
                "priority": Priority(q.priority).name,
                "scheduled_at": q.scheduled_at.isoformat(),
                "retries": q.retries,
            }
            for q in sorted(self._queue)
        ]

    async def start_processing(self):
        if self._running_flag:
            return
        self._running_flag = True
        self._process_task = asyncio.create_task(self._process_loop())
        self.logger.info("queue_processor_started")

    async def stop_processing(self):
        self._running_flag = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        self.logger.info("queue_processor_stopped")

    async def _process_loop(self):
        while self._running_flag:
            try:
                queued = await self.dequeue()
                if queued and self._scan_callback:
                    asyncio.create_task(self._execute_scan(queued))
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("queue_process_error", error=str(e))
                await asyncio.sleep(5)

    async def _execute_scan(self, queued: QueuedScan):
        try:
            success = await self._scan_callback(queued.scan_id)
            await self.complete(queued.queue_id, success=success)
        except Exception as e:
            await self.complete(queued.queue_id, success=False, error=str(e))


scan_queue = ScanQueue()
