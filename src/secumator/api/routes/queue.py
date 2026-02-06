from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Literal
from secumator.core import get_logger, scan_queue, Priority

router = APIRouter()
logger = get_logger("api.queue")


class QueueScanRequest(BaseModel):
    scan_id: int
    priority: Literal["critical", "high", "normal", "low"] = "normal"
    scheduled_at: datetime | None = None
    options: dict[str, Any] | None = None


class QueueStatusResponse(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int
    rate_limit_remaining: int
    is_processing: bool


class QueueItemResponse(BaseModel):
    queue_id: str
    scan_id: int
    priority: str
    scheduled_at: str
    retries: int


@router.post("/queue/enqueue", response_model=dict)
async def enqueue_scan(request: QueueScanRequest):
    priority_map = {
        "critical": Priority.CRITICAL,
        "high": Priority.HIGH,
        "normal": Priority.NORMAL,
        "low": Priority.LOW,
    }

    queue_id = await scan_queue.enqueue(
        scan_id=request.scan_id,
        priority=priority_map.get(request.priority, Priority.NORMAL),
        scheduled_at=request.scheduled_at,
        options=request.options,
    )

    logger.info("scan_enqueued_via_api", queue_id=queue_id, scan_id=request.scan_id)

    return {"queue_id": queue_id, "scan_id": request.scan_id, "status": "queued"}


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    status = scan_queue.get_status()
    return QueueStatusResponse(**status)


@router.get("/queue/items", response_model=list[QueueItemResponse])
async def list_queue_items():
    items = scan_queue.get_queue_items()
    return [QueueItemResponse(**item) for item in items]


@router.post("/queue/{queue_id}/cancel")
async def cancel_queued_scan(queue_id: str):
    success = await scan_queue.cancel(queue_id)
    if not success:
        raise HTTPException(status_code=404, detail="Queue item not found or already running")
    return {"status": "cancelled", "queue_id": queue_id}


@router.post("/queue/start")
async def start_queue_processing():
    await scan_queue.start_processing()
    return {"status": "processing_started"}


@router.post("/queue/stop")
async def stop_queue_processing():
    await scan_queue.stop_processing()
    return {"status": "processing_stopped"}
