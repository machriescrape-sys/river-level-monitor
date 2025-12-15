import csv
import os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

CSV_FILE = "machrie_water_levels.csv"

# Start Playwright and scrape river level & timestamp (example)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://riverlevels.uk/machrie-water-monyquil-farm")
    page.wait_for_load_state("networkidle")

    # Replace these selectors with actual ones
    river_level = page.query_selector(".station-level").inner_text()
    measurement_time = page.query_selector(".station-time").inner_text()
    browser.close()

# Convert measurement_time to UTC ISO
# Adjust parsing depending on the format of measurement_time
measurement_dt = datetime.strptime(measurement_time, "%Y-%m-%d %H:%M")
measurement_dt_utc = measurement_dt.astimezone(timezone.utc)
ts_iso = measurement_dt_utc.isoformat().replace("+00:00", "Z")

# Load existing timestamps
existing_ts = set()
if os.path.isfile(CSV_FILE):
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            ts, _ = line.strip().split(",")
            existing_ts.add(ts)

# Append only if timestamp is new
with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not existing_ts:
        writer.writerow(["measurement_time_utc", "river_level"])
    if ts_iso not in existing_ts:
        writer.writerow([ts_iso, river_level])
        print(f"Added new measurement: {ts_iso}, {river_level}")
    else:
        print(f"Measurement already exists: {ts_iso}")

