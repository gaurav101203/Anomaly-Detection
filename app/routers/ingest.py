from fastapi import APIRouter
from datetime import datetime

from app.models import DataPoint, IngestResponse
from app.redis_client import push_value, get_window
from app.detector import detect
from app.database import save_datapoint, count_anomalies
from app.alerter import fire_alert

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("", response_model=IngestResponse)
async def ingest(data: DataPoint):
    """
    Ingest a single metric data point.
    Runs anomaly detection and fires alerts if needed.
    """
    ts = data.timestamp or datetime.utcnow()

    # 1. Push to Redis sliding window
    await push_value(data.sensor_id, data.metric_name, data.value)

    # 2. Fetch window for detection
    window = await get_window(data.sensor_id, data.metric_name)

    # 3. Run ML detection (window excludes the new point; detect() handles it)
    history = window[:-1]   # everything except the value we just pushed
    result  = detect(history, data.value)

    # 4. Persist to MySQL
    await save_datapoint(
        sensor_id=data.sensor_id,
        metric_name=data.metric_name,
        value=data.value,
        is_anomaly=result.is_anomaly,
        anomaly_score=result.anomaly_score,
        z_score=result.z_score,
        severity=result.severity,
        timestamp=ts,
    )

    # 5. Fire alert (non-blocking — don't let a slow webhook delay the response)
    if result.is_anomaly:
        total = await count_anomalies(data.sensor_id, data.metric_name)
        print(
            f"[ANOMALY] {data.sensor_id}/{data.metric_name} = {data.value:.2f} "
            f"| z={result.z_score:.2f} | severity={result.severity} "
            f"| total_anomalies={total + 1}"
        )
        await fire_alert(
            sensor_id=data.sensor_id,
            metric_name=data.metric_name,
            value=data.value,
            z_score=result.z_score,
            anomaly_score=result.anomaly_score,
            severity=result.severity,
            mean=result.mean,
            std=result.std,
        )

    return IngestResponse(
        received=True,
        sensor_id=data.sensor_id,
        metric_name=data.metric_name,
        value=data.value,
        anomaly_detected=result.is_anomaly,
        severity=result.severity,
        anomaly_score=result.anomaly_score,
        z_score=result.z_score,
        window_size=len(window),
    )
