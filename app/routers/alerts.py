from fastapi import APIRouter, Query
from app.database import get_recent_anomalies
from app.models import AnomalyRecord
from app.redis_client import get_window, get_all_sensor_keys
from app.detector import detect
import numpy as np

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AnomalyRecord])
async def list_anomalies(
    limit: int = Query(default=20, le=200),
    severity: str = Query(default=None),  # filter by "low", "medium", "high"
    sensor_id: str = Query(default=None), # filter by sensor
):
    records = await get_recent_anomalies(
        limit=limit,
        severity=severity,
        sensor_id=sensor_id
    )
    return records


@router.get("/stats/{sensor_id}/{metric_name}")
async def sensor_stats(sensor_id: str, metric_name: str):
    """
    Return live stats for a sensor's current sliding window.
    Useful for the dashboard and debugging.
    """
    from app.database import count_anomalies
    window = await get_window(sensor_id, metric_name)

    if not window:
        return {"error": "No data found for this sensor/metric"}

    arr = np.array(window, dtype=float)
    total = await count_anomalies(sensor_id, metric_name)

    return {
        "sensor_id":       sensor_id,
        "metric_name":     metric_name,
        "window_size":     len(window),
        "mean":            round(float(np.mean(arr)), 3),
        "std":             round(float(np.std(arr)), 3),
        "min":             round(float(np.min(arr)), 3),
        "max":             round(float(np.max(arr)), 3),
        "latest":          window[-1],
        "total_anomalies": total,
    }


@router.get("/active-sensors")
async def active_sensors():
    """Return list of all currently active sensor:metric combinations."""
    keys = await get_all_sensor_keys()
    sensors = []
    for k in keys:
        parts = k.split(":", 1)
        if len(parts) == 2:
            sensors.append({"sensor_id": parts[0], "metric_name": parts[1]})
    return {"count": len(sensors), "sensors": sensors}
