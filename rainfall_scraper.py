import requests
import csv
import os
from datetime import datetime, timezone

STATION_NO = "133115"
CSV_FILE = "monyquil_rainfall_hourly.csv"

url = (
    "https://timeseries.sepa.org.uk/KiWIS/KiWIS"
    "?service=kisters"
    "&type=queryServices"
    "&datasource=0"
    "&request=getTimeseriesValues"
    f"&ts_path=1/{STATION_NO}/RE/Hour.Total"
    "&returnfields=Timestamp,Value"
)

response = requests.get(url, timeout=30)
response.raise_for_status()
data = response.json()

file_exists = os.path.isfile(CSV_FILE)

with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow(["timestamp_utc", "rainfall_mm"])

    for row in data.get("values", []):
        ts = datetime.fromisoformat(row["Timestamp"]).astimezone(timezone.utc)
        writer.writerow([
            ts.isoformat().replace("+00:00", "Z"),
            row["Value"]
        ])

print("Hourly rainfall data updated")
