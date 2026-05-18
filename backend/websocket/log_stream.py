import json
from typing import Dict, List
from fastapi import WebSocket

class LogStreamManager:
    """Manages WebSocket connections for real-time log streaming."""

    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        """Accept a WebSocket connection for a task."""
        await websocket.accept()
        if task_id not in self.connections:
            self.connections[task_id] = []
        self.connections[task_id].append(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if task_id in self.connections:
            if websocket in self.connections[task_id]:
                self.connections[task_id].remove(websocket)

    async def send_log(self, task_id: str, message: Dict):
        """Send a log message to all connected clients for a task."""
        if task_id not in self.connections:
            return

        disconnected = []
        for websocket in self.connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(task_id, websocket)

    async def broadcast(self, task_id: str, message: str, level: str = "INFO"):
        """Broadcast a message to all connected clients."""
        await self.send_log(task_id, {
            "type": "log",
            "level": level,
            "message": message,
        })

# Global instance
log_stream_manager = LogStreamManager()
