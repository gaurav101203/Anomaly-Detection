from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ─── SQLAlchemy DB model ───────────────────────────────────────────────────────

class DataPointDB(Base):
    __tablename__ = "data_points"

    id            = Column(Integer, primary_key=True, index=True)
    sensor_id     = Column(String(100), index=True, nullable=False)
    metric_name   = Column(String(100), nullable=False)
    value         = Column(Float, nullable=False)
    timestamp     = Column(DateTime, default=datetime.utcnow, index=True)
    is_anomaly    = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    z_score       = Column(Float, default=0.0)
    severity      = Column(String(20), default="none")


# ─── Pydantic request / response schemas ──────────────────────────────────────

class DataPoint(BaseModel):
    sensor_id:   str   = Field(..., example="my_laptop")
    metric_name: str   = Field(..., example="cpu_usage")
    value:       float = Field(..., example=42.5)
    timestamp:   Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "my_laptop",
                "metric_name": "cpu_usage",
                "value": 87.3
            }
        }


class IngestResponse(BaseModel):
    received:         bool
    sensor_id:        str
    metric_name:      str
    value:            float
    anomaly_detected: bool
    severity:         str
    anomaly_score:    float
    z_score:          float
    window_size:      int


class AnomalyRecord(BaseModel):
    id:            int
    sensor_id:     str
    metric_name:   str
    value:         float
    timestamp:     datetime
    anomaly_score: float
    z_score:       float
    severity:      str

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    sensor_id:        str
    metric_name:      str
    window_size:      int
    mean:             float
    std:              float
    min:              float
    max:              float
    latest:           float
    total_anomalies:  int
