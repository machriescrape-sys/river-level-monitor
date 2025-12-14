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

    # Wait for ANY text that looks like a level (e.g. 0.79m)
    page.wait_for_selector("text=/\\d+(\\.\\d+)?m/", timeout=60000)

    level = None
    measurement_time = None

    # Find all visible text nodes
    texts = page.locator("body").inner_text().splitlines()

    for i, line in enumerate(texts):
        line = line.strip()
        if re.fullmatch(r"\d+(\.\d+)?m", line):
            level = line

            # The timestamp is usually the next non-empty line
            for next_line in texts[i + 1 : i + 5]:
                if "At" in next_line:
                    measurement_time = next_line.strip()
                    break
            break

    browser.close()

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
