import requests
import csv
from datetime import datetime
import os

# JSON data endpoint used by the site
URL = "https://riverlevels.uk/api/station/machrie-water-monyquil-farm"

CSV_FILE = "machrie_water_levels.csv"

response = requests.get(URL, timeout=15)
response.raise_for_status()

data = response.json()

# Extract fields
level = f"{data['latest_reading']['value']}m"
measurement_time = data['latest_reading']['dateTime']

scrape_time = datetime.utcnow().isoformat()

file_exists = os.path.isfile(CSV_FILE)

with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "scrape_time_utc",
            "river_level",
            "measurement_time"
        ])

    writer.writerow([
        scrape_time,
        level,
        measurement_time
    ])

print("Saved:", level, measurement_time)
