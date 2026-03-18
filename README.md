# 🔬 Real-time Anomaly Detection API

> A production-grade backend that ingests live system metrics, detects anomalies using **Isolation Forest + Z-score**, and fires real-time alerts — built with FastAPI, Redis, MySQL, and Docker.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)
![Redis](https://img.shields.io/badge/Redis-7.0-red?style=flat-square&logo=redis)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)

---

## 🎯 What it does

Most monitoring tools just *show* you data. This system *understands* it.

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

| Layer | Technology | Purpose |
|---|---|---|
| API | FastAPI + uvicorn | Async REST + WebSocket endpoints |
| Buffer | Redis (sliding window) | Low-latency in-memory time-series |
| Detection | scikit-learn Isolation Forest | Context-aware anomaly detection |
| Detection | Z-score (NumPy) | Fast statistical outlier detection |
| Storage | MySQL + SQLAlchemy async | Persistent anomaly log |
| Streaming | psutil | Live PC metrics (CPU, RAM, disk, network) |
| Alerts | httpx webhooks | Slack + custom endpoint notifications |
| Deploy | Docker Compose | One-command setup for all services |

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running

### 1. Clone and start

```bash
git clone https://github.com/YOUR_USERNAME/anomaly-detector.git
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

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Ingest a data point, returns anomaly result instantly |
| `GET` | `/alerts` | List anomalies — filter by `severity`, `sensor_id`, `limit` |
| `GET` | `/alerts/stats/{sensor_id}/{metric}` | Live stats for any sensor |
| `GET` | `/alerts/active-sensors` | All currently active sensors |
| `WS` | `/stream/{sensor_id}/{metric}` | WebSocket live data stream |

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

**Isolation Forest** — an ensemble of random trees that isolates outliers by how few splits it takes to separate a point from the rest of the data. Catches complex, contextual anomalies that Z-score misses (e.g. a value that is not statistically extreme but is unusual *in context*).

A point is flagged as anomalous if **either** method triggers.

| Z-score | Severity |
|---------|----------|
| > 2.0σ | 🟢 Low |
| > 2.5σ | 🟡 Medium |
| > 3.5σ | 🔴 High |

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

## 📁 Project Structure

```
anomaly-detector/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── models.py            # Pydantic + SQLAlchemy models
│   ├── database.py          # Async MySQL (aiomysql)
│   ├── redis_client.py      # Sliding window buffer
│   ├── detector.py          # Isolation Forest + Z-score engine
│   ├── alerter.py           # Slack + webhook alerts
│   └── routers/
│       ├── ingest.py        # POST /ingest
│       ├── stream.py        # WebSocket /stream
│       └── alerts.py        # GET /alerts (with filters)
├── scripts/
│   └── pc_metrics_streamer.py   # Streams real PC metrics via psutil
├── dashboard/
│   └── index.html           # Live dark-mode monitoring dashboard
├── wait-for-db.py           # Pre-startup DB readiness check
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🔔 Slack Alerts (optional)

Add your Slack webhook URL to `docker-compose.yml`:

```yaml
environment:
  - SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/HERE
```

You'll get alerts like:

```
🔴 Anomaly detected on `server_01`
Metric: cpu_usage  |  Value: 97.30
Severity: HIGH     |  Z-score: 5.42σ
Normal range: 14.2 ± 3.1
```

---

## 💡 Extending the Project

The ingestion layer is **data-agnostic** — swap `pc_metrics_streamer.py` for any data source:

```python
# Crypto prices (CoinGecko — no API key needed)
price = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()["bitcoin"]["usd"]
requests.post("http://localhost:8000/ingest", json={"sensor_id": "crypto", "metric_name": "btc_usd", "value": price})

# Weather data (Open-Meteo — no API key needed)
temp = requests.get("https://api.open-meteo.com/v1/forecast?latitude=19.07&longitude=72.87&current=temperature_2m").json()["current"]["temperature_2m"]
requests.post("http://localhost:8000/ingest", json={"sensor_id": "mumbai", "metric_name": "temperature", "value": temp})
```

---

## 📄 License

MIT
