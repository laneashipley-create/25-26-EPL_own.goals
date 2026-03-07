"""
One-off migration: import existing CSV and timeline files into Supabase.

Run once after setting up Supabase to avoid losing existing data.
  - schedule.csv → schedule table
  - data/timelines/*.json → match_timelines table (requires schedule rows first)
  - own_goals.csv → own_goals table

Requires USE_SUPABASE=True (config_local has SUPABASE_KEY).
"""

import csv
import json
import os

from config import USE_SUPABASE, SCHEDULE_CSV, OWN_GOALS_CSV, TIMELINES_DIR, SEASON_ID


def migrate_schedule():
    """Import schedule.csv into schedule table."""
    if not os.path.exists(SCHEDULE_CSV):
        print(f"  Skipping schedule — {SCHEDULE_CSV} not found")
        return 0
    rows = []
    with open(SCHEDULE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    if not rows:
        return 0
    import db
    season_id = db.get_or_create_season()
    db.upsert_schedule(season_id, rows)
    print(f"  Migrated {len(rows)} schedule rows")
    return len(rows)


def migrate_timelines():
    """Import timeline JSON files into match_timelines table."""
    import db
    season_id = db.get_or_create_season()
    if not os.path.isdir(TIMELINES_DIR):
        print(f"  Skipping timelines — {TIMELINES_DIR} not found")
        return 0
    files = [f for f in os.listdir(TIMELINES_DIR) if f.endswith(".json")]
    count = 0
    for filename in files:
        sport_event_id = filename.replace("sr_sport_event_", "sr:sport_event:").replace(".json", "")
        row = db.get_schedule_by_sport_event_id(season_id, sport_event_id)
        if not row:
            continue
        filepath = os.path.join(TIMELINES_DIR, filename)
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        db.upsert_timeline(row["id"], data)
        count += 1
    print(f"  Migrated {count} timeline files")
    return count


def migrate_own_goals():
    """Import own_goals.csv into own_goals table."""
    if not os.path.exists(OWN_GOALS_CSV):
        print(f"  Skipping own_goals — {OWN_GOALS_CSV} not found")
        return 0
    rows = []
    with open(OWN_GOALS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    if not rows:
        return 0
    import db
    db.upsert_own_goals(rows, replace=True)  # Replace with CSV content
    print(f"  Migrated {len(rows)} own_goal rows")
    return len(rows)


def main():
    if not USE_SUPABASE:
        print("USE_SUPABASE is False. Add SUPABASE_KEY to config_local.py and try again.")
        return
    print("Migrating existing data to Supabase...")
    migrate_schedule()
    migrate_timelines()
    migrate_own_goals()
    print("Migration done.")


if __name__ == "__main__":
    main()
