"""
STEP 3 — Fetch sport_event_timeline for every completed match.

• Reads match IDs from data/schedule.csv
• Only fetches matches with status in COMPLETED_STATUSES
• Caches raw JSON responses in data/timelines/<sport_event_id>.json
  so re-runs skip already-fetched matches (safe to interrupt and resume)
• Respects the 1 req/sec trial-key rate limit

Run independently to pull new timelines without touching earlier data.
"""

import csv
import json
import os
import time
import urllib.request
import urllib.error

from config import (
    API_KEY,
    BASE_URL,
    SCHEDULE_CSV,
    TIMELINES_DIR,
    COMPLETED_STATUSES,
    REQUEST_DELAY_SECONDS,
)


def load_completed_matches(csv_path: str) -> list[dict]:
    """Return rows from schedule CSV where status is completed."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"{csv_path} not found — run step2_get_schedule.py first"
        )
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["status"] in COMPLETED_STATUSES:
                rows.append(row)
    return rows


def fetch_timeline(sport_event_id: str) -> dict:
    """Fetch the timeline JSON for a single sport event."""
    url = f"{BASE_URL}/sport_events/{sport_event_id}/timeline.json?api_key={API_KEY}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def cache_path(sport_event_id: str) -> str:
    safe_id = sport_event_id.replace(":", "_")
    return os.path.join(TIMELINES_DIR, f"{safe_id}.json")


def main():
    os.makedirs(TIMELINES_DIR, exist_ok=True)

    matches = load_completed_matches(SCHEDULE_CSV)
    print(f"Completed matches to process: {len(matches)}")

    fetched = 0
    skipped = 0
    errors = 0

    for i, match in enumerate(matches, 1):
        event_id = match["sport_event_id"]
        out_path = cache_path(event_id)

        if os.path.exists(out_path):
            skipped += 1
            continue

        home = match["home_team"]
        away = match["away_team"]
        date = match["start_time"][:10]
        print(f"[{i}/{len(matches)}] Fetching {date}  {home} vs {away}  ({event_id})")

        try:
            data = fetch_timeline(event_id)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            fetched += 1
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} — skipping")
            errors += 1
        except Exception as e:
            print(f"  Error: {e} — skipping")
            errors += 1

        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\nDone.")
    print(f"  Newly fetched : {fetched}")
    print(f"  Already cached: {skipped}")
    print(f"  Errors        : {errors}")
    print(f"\nTimelines saved in: {TIMELINES_DIR}/")


if __name__ == "__main__":
    main()
