from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
import os
import re

URL = "https://riverlevels.uk/machrie-water-monyquil-farm"
CSV_FILE = "machrie_water_levels.csv"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, timeout=60000)

    page.wait_for_load_state("networkidle")

    # Dump all visible text that contains 'm'
    texts = page.locator("text=/m$/").all_inner_texts()

    print("FOUND TEXTS ENDING IN 'm':")
    for t in texts:
        print("-", t)

    browser.close()

raise RuntimeError("Stopping after text dump")

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
