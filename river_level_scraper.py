from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
import os

URL = "https://riverlevels.uk/machrie-water-monyquil-farm"
CSV_FILE = "machrie_water_levels.csv"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, timeout=60000)

    # Wait until any text like "0.79m" appears
    page.wait_for_function(
        "() => document.body.innerText.match(/\\d+(\\.\\d+)?m/)"
    )

    body_text = page.inner_text("body")

    browser.close()

# ---- Extract level ----
level = None
for token in body_text.split():
    if token.endswith("m") and token[:-1].replace(".", "").isdigit():
        level = token
        break

# ---- Extract measurement time ----
measurement_time = None
for line in body_text.splitlines():
    if line.strip().startswith("At "):
        measurement_time = line.strip()
        break

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
