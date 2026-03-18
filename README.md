# 🔬 Real-time Anomaly Detection API

> A production-grade backend that ingests live system metrics, detects anomalies using **Isolation Forest + Z-score**, and fires real-time alerts — built with FastAPI, Redis, MySQL, and Docker.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)
![Redis](https://img.shields.io/badge/Redis-7.0-red?style=flat-square&logo=redis)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)

---

<img width="1920" height="1080" alt="Screenshot (40)" src="https://github.com/user-attachments/assets/53574e90-31a5-49b1-b859-e5a33e78facc" />

## 🎯 What it does

Most monitoring tools just _show_ you data. This system _understands_ it.

Every incoming data point is evaluated against a **sliding window of the last 100 readings** using two complementary ML methods. If either method flags it as unusual for that sensor's historical pattern, an alert fires instantly — no manual threshold-setting required.

**Real use cases this architecture maps to:**

- Server fleet monitoring across hundreds of microservices
- IoT sensor networks detecting equipment failure before it happens
- Financial fraud detection (same math, different data source)
- Patient vitals monitoring in healthcare systems

---

## 🏗️ Architecture

```
Live data sources (psutil / IoT / APIs)
              │
              ▼  POST /ingest
    ┌─────────────────────────┐
    │     FastAPI service      │
    │                         │
    │  Redis sliding window   │──► Isolation Forest + Z-score
    │  (last 100 readings)    │              │
    │                         │         anomaly?
    │  MySQL persistence      │──► Slack / webhook alert
    └─────────────────────────┘
              │
              ▼  ws://localhost/stream/{sensor}/{metric}
       Live dashboard (real-time charts + alert feed)
```

---

## ⚙️ Tech Stack

| Layer     | Technology                    | Purpose                                   |
| --------- | ----------------------------- | ----------------------------------------- |
| API       | FastAPI + uvicorn             | Async REST + WebSocket endpoints          |
| Buffer    | Redis (sliding window)        | Low-latency in-memory time-series         |
| Detection | scikit-learn Isolation Forest | Context-aware anomaly detection           |
| Detection | Z-score (NumPy)               | Fast statistical outlier detection        |
| Storage   | MySQL + SQLAlchemy async      | Persistent anomaly log                    |
| Streaming | psutil                        | Live PC metrics (CPU, RAM, disk, network) |
| Alerts    | httpx webhooks                | Slack + custom endpoint notifications     |
| Deploy    | Docker Compose                | One-command setup for all services        |

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running

### 1. Clone and start

```bash
git clone https://github.com/gaurav101203/anomaly-detector.git
cd anomaly-detector
docker compose up --build
```

Wait for:

```
api-1  | INFO: Application startup complete.
```

### 2. Stream live PC metrics

```bash
pip install psutil requests
python scripts/pc_metrics_streamer.py
```

### 3. Open the dashboard

```
http://localhost:8000/dashboard    ← live charts + anomaly feed
http://localhost:8000/docs         ← Swagger UI (test all endpoints)
```

### 4. Trigger a real anomaly 🔴

```bash
# Hammer the CPU — watch the dashboard light up
python -c "import math; [math.factorial(100000) for _ in range(9999999)]"
```

---

## 📡 API Endpoints

| Method | Endpoint                             | Description                                                 |
| ------ | ------------------------------------ | ----------------------------------------------------------- |
| `POST` | `/ingest`                            | Ingest a data point, returns anomaly result instantly       |
| `GET`  | `/alerts`                            | List anomalies — filter by `severity`, `sensor_id`, `limit` |
| `GET`  | `/alerts/stats/{sensor_id}/{metric}` | Live stats for any sensor                                   |
| `GET`  | `/alerts/active-sensors`             | All currently active sensors                                |
| `WS`   | `/stream/{sensor_id}/{metric}`       | WebSocket live data stream                                  |

### Example — ingest a reading

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"sensor_id": "server_01", "metric_name": "cpu_usage", "value": 97.3}'
```

```json
{
  "received": true,
  "sensor_id": "server_01",
  "metric_name": "cpu_usage",
  "value": 97.3,
  "anomaly_detected": true,
  "severity": "high",
  "anomaly_score": 0.1823,
  "z_score": 5.42,
  "window_size": 87
}
```

### Example — query only high severity anomalies

```bash
curl "http://localhost:8000/alerts?severity=high&limit=20"
```

---

## 🧠 Detection Logic

Two methods run on **every single data point**:

**Z-score** — measures how many standard deviations the new value is from the sliding window mean. Fast, interpretable, great for simple spikes.

**Isolation Forest** — an ensemble of random trees that isolates outliers by how few splits it takes to separate a point from the rest of the data. Catches complex, contextual anomalies that Z-score misses (e.g. a value that is not statistically extreme but is unusual _in context_).

A point is flagged as anomalous if **either** method triggers.

| Z-score | Severity  |
| ------- | --------- |
| > 2.0σ  | 🟢 Low    |
| > 2.5σ  | 🟡 Medium |
| > 3.5σ  | 🔴 High   |

---

## 📊 Data Volume & Tuning

The streamer collects 8 metrics every 5 seconds by default. You can tune this in `scripts/pc_metrics_streamer.py`:

```python
INTERVAL = 5.0   # seconds between collections
```

Detection sensitivity is tunable in `app/detector.py`:

```python
z_anomaly = z_score > 2.0    # lower = more sensitive
```

This matters at scale — at 1-second intervals across 8 metrics on 500 servers, you generate **240,000 data points per minute**. Configurable intervals and severity filtering are essential for keeping the system usable.

---
