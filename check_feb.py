import csv, os
from config import SCHEDULE_CSV, TIMELINES_DIR, COMPLETED_STATUSES

with open(SCHEDULE_CSV, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

feb = [r for r in rows if "2026-02-01" <= r["start_time"][:10] <= "2026-02-25"]
completed = [r for r in feb if r["status"] in COMPLETED_STATUSES]
print(f"Feb 1-25 in schedule: {len(feb)} total, {len(completed)} completed")

def cache_path(eid):
    return os.path.join(TIMELINES_DIR, eid.replace(":", "_") + ".json")

cached  = [r for r in completed if os.path.exists(cache_path(r["sport_event_id"]))]
missing = [r for r in completed if not os.path.exists(cache_path(r["sport_event_id"]))]
print(f"Already cached: {len(cached)}   Missing / new: {len(missing)}")
if missing:
    print("\nNot yet cached:")
    for r in sorted(missing, key=lambda x: x["start_time"]):
        print(f"  {r['start_time'][:10]}  {r['home_team']} vs {r['away_team']}  [{r['status']}]")
