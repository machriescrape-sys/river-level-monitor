import requests
import csv
import os
from datetime import datetime, timezone

STATION_ID = "133115"
CSV_FILE = "monyquil_rainfall.csv"

URL = (
    "https://www2.sepa.org.uk/api/Timeseries/Readings"
    f"?station={STATION_ID}&parameter=rainfall"
)

response = requests.get(URL, timeout=30)
response.raise_for_status()

data = response.json()

file_exists = os.path.isfile(CSV_FILE)

with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "timestamp_utc",
            "rainfall_mm"
        ])

    for item in data["items"]:
        ts = datetime.fromisoformat(
            item["timestamp"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)

        writer.writerow([
            ts.isoformat().replace("+00:00", "Z"),
            item["value"]
        ])

print("Rainfall data updated")
