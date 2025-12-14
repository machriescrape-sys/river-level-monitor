import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os

URL = "https://riverlevels.uk/machrie-water-monyquil-farm"
CSV_FILE = "machrie_water_levels.csv"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=15)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Extract river level
level_elem = soup.find("h2")
level = level_elem.get_text(strip=True) if level_elem else None

# Extract measurement time
time_elem = level_elem.find_next_sibling("p") if level_elem else None
measurement_time = time_elem.get_text(strip=True) if time_elem else None

if not level or not measurement_time:
    raise RuntimeError("Failed to scrape river data")

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
