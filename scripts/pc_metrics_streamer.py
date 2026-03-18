"""
PC Metrics Streamer
───────────────────
Streams your real CPU, RAM, disk, and network metrics to the anomaly
detection API every second using psutil.

Usage:
    pip install psutil requests
    python scripts/pc_metrics_streamer.py

To trigger a real anomaly:
    - Open many browser tabs
    - Run a CPU-heavy script
    - Fill up RAM with a large file load
The system will detect and alert within seconds.
"""

import time
import requests
import psutil
import argparse
from datetime import datetime

API_URL   = "http://localhost:8000/ingest"
SENSOR_ID = "my_laptop"
INTERVAL  = 5.0   # seconds between readings


def send(metric_name: str, value: float, verbose: bool = True):
    try:
        resp = requests.post(API_URL, json={
            "sensor_id":   SENSOR_ID,
            "metric_name": metric_name,
            "value":       round(value, 2),
            "timestamp":   datetime.utcnow().isoformat(),
        }, timeout=3)

        data = resp.json()

        if data.get("anomaly_detected"):
            print(
                f"  🔴 ANOMALY  {metric_name:20s} = {value:7.2f} "
                f"| z={data['z_score']:.2f} | severity={data['severity'].upper()}"
            )
        elif verbose:
            print(
                f"  ✅ normal   {metric_name:20s} = {value:7.2f} "
                f"| window={data['window_size']}"
            )
    except requests.exceptions.ConnectionError:
        print(f"  ⚠️  Cannot reach API at {API_URL} — is it running?")
    except Exception as e:
        print(f"  ⚠️  Error sending {metric_name}: {e}")


def collect_and_send(verbose: bool):
    # CPU usage per core + overall
    cpu_total = psutil.cpu_percent(interval=None)
    send("cpu_total_pct", cpu_total, verbose)

    for i, pct in enumerate(psutil.cpu_percent(percpu=True)):
        send(f"cpu_core_{i}_pct", pct, verbose)

    # RAM
    mem = psutil.virtual_memory()
    send("ram_used_pct",   mem.percent, verbose)
    send("ram_used_mb",    mem.used / 1024 / 1024, verbose)

    # Disk I/O
    disk_io = psutil.disk_io_counters()
    if disk_io:
        send("disk_read_mb_s",  disk_io.read_bytes  / 1024 / 1024, verbose)
        send("disk_write_mb_s", disk_io.write_bytes / 1024 / 1024, verbose)

    # Network I/O
    net = psutil.net_io_counters()
    send("net_sent_mb_s",  net.bytes_sent / 1024 / 1024, verbose)
    send("net_recv_mb_s",  net.bytes_recv / 1024 / 1024, verbose)

    # CPU temperature (Linux / Mac with sensors; Windows may not support)
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for chip, entries in temps.items():
                for entry in entries[:1]:   # first sensor per chip
                    send(f"temp_{chip}", entry.current, verbose)
    except (AttributeError, NotImplementedError):
        pass   # not supported on all platforms


def main():
    parser = argparse.ArgumentParser(description="Stream PC metrics to anomaly detector")
    parser.add_argument("--quiet", action="store_true", help="Only print anomalies")
    args = parser.parse_args()

    verbose = not args.quiet
    print(f"Streaming PC metrics to {API_URL} every {INTERVAL}s")
    print(f"Sensor ID: {SENSOR_ID}")
    print("Press Ctrl+C to stop.\n")

    # Warm up psutil (first call always returns 0.0 for cpu_percent)
    psutil.cpu_percent(interval=None)
    time.sleep(0.1)

    while True:
        t0 = time.time()
        if verbose:
            print(f"── {datetime.now().strftime('%H:%M:%S')} ──────────────────")
        collect_and_send(verbose)
        elapsed = time.time() - t0
        sleep_time = max(0, INTERVAL - elapsed)
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
