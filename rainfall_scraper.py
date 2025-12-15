import time
import requests
import csv
import os
from datetime import datetime, timezone

STATION_NO = "133115"
CSV_FILE = "monyquil_rainfall_hourly.csv"

URL = (
    "https://timeseries.sepa.org.uk/KiWIS/KiWIS"
    "?service=kisters"
    "&type=queryServices"
    "&datasource=0"
    "&request=getTimeseriesValues"
    f"&ts_path=1/{STATION_NO}/RE/Hour.Total"
    "&returnfields=Timestamp,Value"
)

headers = {
    "User-Agent": "river-level-monitor/1.0 (contact: github actions)"
}

# ---- Request with retry ----
response = None
for attempt in range(5):
    response = requests.get(URL, headers=headers, timeout=30)

    if response.status_code == 429:
        wait = 15 * (attempt + 1)
        print(f"SEPA rate-limited (429). Waiting {wait}s...")
        time.sleep(wait)
        continue

    if response.status_code != 200:
        print("Non-200 response from SEPA")
        print("Status:", response.status_code)
        print("Body preview:", response.text[:300])
        exit(0)  # do NOT fail the workflow

    break
else:
    print("Failed to fetch rainfall data after retries")
    exit(0)

# ---- Ensure response is JSON ----
content_type = response.headers.get("Content-Type", "")
if "json" not in content_type.lower():
    print("SEPA returned non-JSON response")
    print("Content-Type:", content_type)
    print("Body preview:", response.text[:300])
    exit(0)

data = response.json()

# ---- Load existing timestamps ----
existing_ts = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        next(f, None)
        for line in f:
            ts, _ = line.strip().split(",")
            existing_ts.add(ts)

# ---- Write new rows only ----
with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not existing_ts:
        writer.writerow(["timestamp_utc", "rainfall_mm"])

    for row in data.get("values", []):
        ts = datetime.fromisoformat(row["Timestamp"]).astimezone(timezone.utc)
        ts_iso = ts.isoformat().replace("+00:00", "Z")

        if ts_iso not in existing_ts:
            writer.writerow([ts_iso, row["Value"]])

print("Rainfall scraper completed successfully")
