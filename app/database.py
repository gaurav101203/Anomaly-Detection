import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models import Base, DataPointDB
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "mysql://user:password@localhost:3306/anomaly_db")

# SQLAlchemy needs aiomysql driver for async
ASYNC_DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+aiomysql://")

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables ready.")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def save_datapoint(
    sensor_id: str,
    metric_name: str,
    value: float,
    is_anomaly: bool,
    anomaly_score: float,
    z_score: float,
    severity: str,
    timestamp: datetime = None
):
    async with AsyncSessionLocal() as session:
        record = DataPointDB(
            sensor_id=sensor_id,
            metric_name=metric_name,
            value=value,
            timestamp=timestamp or datetime.utcnow(),
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            z_score=z_score,
            severity=severity
        )
        session.add(record)
        await session.commit()


async def get_recent_anomalies(
    limit: int = 50,
    severity: str = None,
    sensor_id: str = None
) -> list[DataPointDB]:
    async with AsyncSessionLocal() as session:
        query = (
            select(DataPointDB)
            .where(DataPointDB.is_anomaly == True)
            .order_by(DataPointDB.timestamp.desc())
            .limit(limit)
        )
        if severity:
            query = query.where(DataPointDB.severity == severity)
        if sensor_id:
            query = query.where(DataPointDB.sensor_id == sensor_id)

        result = await session.execute(query)
        return result.scalars().all()


async def count_anomalies(sensor_id: str, metric_name: str) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count(DataPointDB.id))
            .where(DataPointDB.sensor_id == sensor_id)
            .where(DataPointDB.metric_name == metric_name)
            .where(DataPointDB.is_anomaly == True)
        )
        return result.scalar() or 0
