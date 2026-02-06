from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Any
import json
import asyncio
from secumator.core import get_logger

router = APIRouter()
logger = get_logger("api.websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, scan_id: str | None = None, accept: bool = True):
        if accept:
            await websocket.accept()
        channel = scan_id or "global"
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = []
            self.active_connections[channel].append(websocket)
        logger.info("websocket_connected", channel=channel)

    async def disconnect(self, websocket: WebSocket, scan_id: str | None = None):
        channel = scan_id or "global"
        async with self._lock:
            if channel in self.active_connections:
                if websocket in self.active_connections[channel]:
                    self.active_connections[channel].remove(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]
        logger.info("websocket_disconnected", channel=channel)

    async def broadcast(self, message: dict[str, Any], scan_id: str | None = None):
        channel = scan_id or "global"
        async with self._lock:
            connections = self.active_connections.get(channel, []).copy()
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                await self.disconnect(connection, scan_id)

    async def broadcast_global(self, message: dict[str, Any]):
        async with self._lock:
            all_connections = []
            for connections in self.active_connections.values():
                all_connections.extend(connections)
        
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe":
                scan_id = message.get("scan_id")
                if scan_id:
                    await manager.disconnect(websocket)
                    await manager.connect(websocket, str(scan_id), accept=False)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@router.websocket("/ws/scan/{scan_id}")
async def websocket_scan(websocket: WebSocket, scan_id: int):
    await manager.connect(websocket, str(scan_id))
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "scan_id": scan_id})
    except WebSocketDisconnect:
        await manager.disconnect(websocket, str(scan_id))


async def emit_scan_progress(scan_id: int, progress: int, status: str, message: str = ""):
    await manager.broadcast(
        {
            "type": "scan_progress",
            "scan_id": scan_id,
            "progress": progress,
            "status": status,
            "message": message,
        },
        str(scan_id),
    )
    await manager.broadcast_global(
        {
            "type": "scan_progress",
            "scan_id": scan_id,
            "progress": progress,
            "status": status,
            "message": message,
        }
    )


async def emit_finding(scan_id: int, finding: dict[str, Any]):
    await manager.broadcast(
        {"type": "finding", "scan_id": scan_id, "finding": finding},
        str(scan_id),
    )


async def emit_scan_complete(scan_id: int, summary: dict[str, Any]):
    await manager.broadcast(
        {"type": "scan_complete", "scan_id": scan_id, "summary": summary},
        str(scan_id),
    )
    await manager.broadcast_global(
        {"type": "scan_complete", "scan_id": scan_id, "summary": summary}
    )
