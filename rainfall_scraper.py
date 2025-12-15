import time
import requests
import csv
import os
from datetime import datetime, timezone, timedelta

# ----------------------------
# Configuration
# ----------------------------
STATION_NO = "133115"
CSV_FILE = "monyquil_rainfall_hourly.csv"
HOURS_LOOKBACK = 24  # fetch the last 24 hours

BASE_URL = (
    "https://timeseries.sepa.org.uk/KiWIS/KiWIS"
    "?service=kisters"
    "&type=queryServices"
    "&datasource=0"
    "&request=getTimeseriesValues"
    f"&ts_path=1/{STATION_NO}/RE/Hour.Total"
    "&returnfields=Timestamp,Value"
    "&format=json"
)

HEADERS = {
    "User-Agent": "river-level-monitor/1.0 (github actions)"
}

# ----------------------------
# Determine starting timestamp
# ----------------------------
now_utc = datetime.now(timezone.utc)
from_time = now_utc - timedelta(hours=HOURS_LOOKBACK)
from_param = from_time.strftime("%Y-%m-%dT%H:%M:%S")

URL = BASE_URL + f"&from={from_param}"

# ----------------------------
# Request with retry & rate-limit handling
# ----------------------------
response = None
for attempt in range(5):
    response = requests.get(URL, headers=HEADERS, timeout=30)

    if response.status_code == 429:
        wait = 15 * (attempt + 1)
        print(f"SEPA rate-limited (429). Waiting {wait}s...")
        time.sleep(wait)
        continue

    if response.status_code != 200:
        print("Non-200 response from SEPA")
        print("Status:", response.status_code)
        print("Body preview:", response.text[:300])
        exit(0)

    break
else:
    print("Failed to fetch rainfall data after retries")
    exit(0)

# ----------------------------
# Ensure JSON response
# ----------------------------
content_type = response.headers.get("Content-Type", "")
if "json" not in content_type.lower():
    print("SEPA returned non-JSON response")
    print("Content-Type:", content_type)
    print("Body preview:", response.text[:300])
    exit(0)

data = response.json()

# ----------------------------
# Handle SEPA list response
# ----------------------------
if isinstance(data, list):
    if not data:
        print("No rainfall data returned")
        exit(0)
    data = data[0]  # first station object

values = data.get("values")
if not values or not isinstance(values, list):
    print("No rainfall data available")
    exit(0)

# ----------------------------
# Load existing timestamps
# ----------------------------
existing_ts = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            existing_ts.add(row[0])

# ----------------------------
# Write new rows only
# ----------------------------
file_exists = os.path.exists(CSV_FILE)

with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow(["timestamp_utc", "rainfall_mm"])

    new_rows = 0
    for row in values:
        ts = datetime.fromisoformat(row["Timestamp"]).astimezone(timezone.utc)
        ts_iso = ts.isoformat().replace("+00:00", "Z")

        if ts_iso not in existing_ts:
            writer.writerow([ts_iso, row["Value"]])
            new_rows += 1

print(f"Rainfall scraper completed — added {new_rows} new rows")
