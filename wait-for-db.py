"""
Blocks until the MySQL host:port is reachable, then exits.
Used as an entrypoint pre-check before uvicorn starts.
"""
import socket
import time
import sys

host = "db"
port = 3306
timeout = 120   # wait up to 2 minutes
interval = 2

print(f"Waiting for MySQL at {host}:{port}...", flush=True)
start = time.time()

while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            elapsed = round(time.time() - start, 1)
            print(f"MySQL is up after {elapsed}s — starting API.", flush=True)
            sys.exit(0)
    except (socket.error, OSError) as e:
        elapsed = round(time.time() - start, 1)
        if elapsed >= timeout:
            print(f"Timed out waiting for MySQL after {timeout}s. Exiting.", flush=True)
            sys.exit(1)
        print(f"  [{elapsed}s] Not ready yet ({e}), retrying in {interval}s...", flush=True)
        time.sleep(interval)
