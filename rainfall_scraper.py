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
    "&format=json"
)

HEADERS = {
    "User-Agent": "river-level-monitor/1.0 (github actions)"
}

# --------------------------------------------------
# Read latest timestamp from CSV
# --------------------------------------------------
def latest_timestamp_in_csv(csv_file):
    if not os.path.exists(csv_file):
        return None

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        rows = list(reader)

        if not rows:
            return None

        ts = rows[-1][0].replace("Z", "+00:00")
        return datetime.fromisoformat(ts)


latest_ts = latest_timestamp_in_csv(CSV_FILE)

# Current hour (UTC, floored)
now_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

# --------------------------------------------------
# LEVEL 1: Skip request if already up to date
# --------------------------------------------------
if latest_ts and latest_ts >= now_hour:
    print("Rainfall data already up to date — skipping SEPA request")
    exit(0)

# --------------------------------------------------
# LEVEL 2: Request only new data
# --------------------------------------------------
URL = BASE_URL
if latest_ts:
    from_param = latest_ts.strftime("%Y-%m-%dT%H:%M:%S")
    URL += f"&from={from_param}"

# --------------------------------------------------
# Request with retry + rate-limit handling
# --------------------------------------------------
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

# --------------------------------------------------
# Ensure JSON response
# --------------------------------------------------
content_type = response.headers.get("Content-Type", "")
if "json" not in content_type.lower():
    print("SEPA returned non-JSON response")
    print("Content-Type:", content_type)
    print("Body preview:", response.text[:300])
    exit(0)

data = response.json()

values = data.get("values", [])
if not values:
    print("No new rainfall data available")
    exit(0)

# --------------------------------------------------
# Load existing timestamps (duplicate protection)
# --------------------------------------------------
existing_ts = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            existing_ts.add(row[0])

# --------------------------------------------------
# Write new rows only
# --------------------------------------------------
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
