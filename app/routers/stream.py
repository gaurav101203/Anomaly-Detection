import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.redis_client import get_window, get_all_sensor_keys

router = APIRouter(prefix="/stream", tags=["streaming"])

# Track all live WebSocket connections
_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/{sensor_id}/{metric_name}")
async def stream_sensor(websocket: WebSocket, sensor_id: str, metric_name: str):
    """
    WebSocket endpoint — streams the latest window data every second.
    Connect: ws://localhost:8000/stream/{sensor_id}/{metric_name}
    """
    await websocket.accept()
    key = f"{sensor_id}:{metric_name}"
    _connections.setdefault(key, []).append(websocket)

    try:
        while True:
            window = await get_window(sensor_id, metric_name)
            if window:
                payload = {
                    "sensor_id":   sensor_id,
                    "metric_name": metric_name,
                    "latest":      window[-1],
                    "window":      window[-60:],   # last 60 points for the chart
                    "count":       len(window),
                }
                await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        _connections[key].remove(websocket)
    except Exception as e:
        print(f"[ws] error for {key}: {e}")
        if websocket in _connections.get(key, []):
            _connections[key].remove(websocket)


@router.websocket("/all")
async def stream_all(websocket: WebSocket):
    """
    WebSocket that streams ALL active sensors every 2 seconds.
    Connect: ws://localhost:8000/stream/all
    """
    await websocket.accept()
    try:
        while True:
            keys   = await get_all_sensor_keys()
            result = {}
            for k in keys:
                parts = k.split(":", 1)
                if len(parts) == 2:
                    sid, metric = parts
                    window = await get_window(sid, metric)
                    if window:
                        result[k] = {
                            "latest": window[-1],
                            "count":  len(window),
                        }
            await websocket.send_text(json.dumps(result))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
