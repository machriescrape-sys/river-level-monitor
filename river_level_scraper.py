import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
import re

URL = "https://riverlevels.uk/machrie-water-monyquil-farm"
CSV_FILE = "machrie_water_levels.csv"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=15)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Find all h2 elements and look for one that looks like a level (e.g. 0.54m)
level = None
level_elem = None

for h2 in soup.find_all("h2"):
    text = h2.get_text(strip=True)
    if re.match(r"^\d+(\.\d+)?m$", text):
        level = text
        level_elem = h2
        break

# The time is in the paragraph immediately after the level
measurement_time = None
if level_elem:
    p = level_elem.find_next_sibling("p")
    if p:
        measurement_time = p.get_text(strip=True)

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

# DEBUG: show page title and first 500 chars
print("PAGE TITLE:", soup.title)
print("PAGE PREVIEW:")
print(response.text[:500])

raise RuntimeError("Stopping after debug output")
