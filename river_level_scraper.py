from playwright.sync_api import sync_playwright
import csv
from datetime import datetime, timezone
import os
import re

def parse_measurement_time(text):
    """
    Converts:
    'At 9:30am, Wednesday 13th December GMT'
    -> ISO UTC string
    """
    text = text.replace("At ", "").replace(" GMT", "")
    text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', text)

    dt = datetime.strptime(
        text,
        "%I:%M%p, %A %d %B"
    )

    # Year is not included, so assume current year
    dt = dt.replace(year=datetime.utcnow().year, tzinfo=timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")

URL = "https://riverlevels.uk/machrie-water-monyquil-farm"
CSV_FILE = "machrie_water_levels.csv"

def load_existing_measurement_times(csv_file):
    times = set()
    if os.path.isfile(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            next(f, None)  # skip header
            for row in f:
                parts = row.strip().split(",")
                if len(parts) >= 3:
                    times.add(parts[2])  # measurement_time column
    return times

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for attempt in range(3):
        try:
            page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=60000
            )
            break
    except Exception as e:
        if attempt == 2:
            raise
        print("Page load failed, retrying...")
        time.sleep(5)

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

scrape_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
measurement_time_iso = parse_measurement_time(measurement_time)

existing_times = load_existing_measurement_times(CSV_FILE)
file_exists = os.path.isfile(CSV_FILE)

if measurement_time_iso in existing_times:
    print("Measurement already recorded:", measurement_time_iso)
else:
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "scrape_time_utc",
                "river_level",
                "measurement_time_utc"
            ])

        writer.writerow([
            scrape_time,
            level,
            measurement_time_iso
        ])

    print("Saved new measurement:", level, measurement_time_iso)
