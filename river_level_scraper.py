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

    # Wait for headings to load
    page.wait_for_selector("h2", timeout=60000)

    level = None
    measurement_time = None

    h2_elements = page.query_selector_all("h2")

    for h2 in h2_elements:
        text = h2.inner_text().strip()
        if re.match(r"^\d+(\.\d+)?m$", text):
            level = text

            p_tag_handle = h2.evaluate_handle(
                "el => el.nextElementSibling"
            )
            if p_tag_handle:
                p_elem = p_tag_handle.as_element()
                if p_elem:
                    measurement_time = p_elem.inner_text().strip()

            break  # <-- THIS IS NOW CORRECTLY INSIDE THE LOOP

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
