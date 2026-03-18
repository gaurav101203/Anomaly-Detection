from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.redis_client import close_redis
from app.routers import ingest, stream, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    print("Starting up: initialising database...")
    await init_db()
    print("Database ready.")
    yield
    # ── Shutdown ──
    print("Shutting down: closing Redis...")
    await close_redis()


app = FastAPI(
    title="Real-time Anomaly Detection API",
    description=(
        "Ingests live PC metrics (CPU, RAM, disk), runs Isolation Forest + Z-score "
        "anomaly detection, and fires alerts. Built with FastAPI, Redis, MySQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the local dashboard HTML to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(stream.router)
app.include_router(alerts.router)

# Serve the live dashboard (dashboard/index.html)
dashboard_path = os.path.join(os.path.dirname(__file__), "..", "dashboard")
if os.path.isdir(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "Anomaly Detection API",
        "status":  "running",
        "docs":    "/docs",
        "dashboard": "/dashboard",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
