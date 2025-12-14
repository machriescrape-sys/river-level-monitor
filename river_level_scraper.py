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

# DEBUG: show what GitHub Actions is actually receiving
print("PAGE TITLE:", soup.title)
print("PAGE PREVIEW (first 500 chars):")
print(response.text[:500])

raise RuntimeError("Stopping after debug output")
