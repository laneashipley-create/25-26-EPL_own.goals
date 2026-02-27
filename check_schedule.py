"""
Investigate the 393 vs 380 match count.
An EPL season has exactly 380 matches (20 teams x 19 home x 19 away).
The API inflates this by keeping both the original postponed slot AND
the rescheduled replacement as separate entries.
"""
import csv
import json
import urllib.request

from config import API_KEY, BASE_URL, SEASON_ID

with open('data/schedule.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f"Total rows in schedule CSV: {len(rows)}")
print(f"  closed     : {sum(1 for r in rows if r['status'] == 'closed')}")
print(f"  not_started: {sum(1 for r in rows if r['status'] == 'not_started')}")
print(f"  postponed  : {sum(1 for r in rows if r['status'] == 'postponed')}")
print()

# Fetch raw schedule to check for replaced_by fields on postponed events
print("Fetching raw schedule to check 'replaced_by' on postponed fixtures...")
url = f"{BASE_URL}/seasons/{SEASON_ID}/schedules.json?api_key={API_KEY}"
req = urllib.request.Request(url, headers={"Accept": "application/json"})
with urllib.request.urlopen(req, timeout=30) as resp:
    import json
    data = json.loads(resp.read().decode())

postponed = [
    s for s in data['schedules']
    if s.get('sport_event_status', {}).get('status') == 'postponed'
]

print(f"\n{'='*70}")
print(f"{'ORIGINAL DATE':<14} {'MATCHUP':<45} {'REPLACED BY?'}")
print(f"{'='*70}")
has_replacement = 0
no_replacement = 0
for s in postponed:
    se = s['sport_event']
    comps = se.get('competitors', [])
    home = next((c['name'] for c in comps if c['qualifier'] == 'home'), '?')
    away = next((c['name'] for c in comps if c['qualifier'] == 'away'), '?')
    date = se['start_time'][:10]
    replaced_by = se.get('replaced_by', None)
    if replaced_by:
        has_replacement += 1
        print(f"{date:<14} {home} vs {away:<30} -> {replaced_by}")
    else:
        no_replacement += 1
        print(f"{date:<14} {home} vs {away:<30} -> NO RESCHEDULED DATE YET")

print(f"\nPostponed with rescheduled replacement : {has_replacement}")
print(f"Postponed with no replacement yet      : {no_replacement}")
print()
print(f"Explanation:")
print(f"  380 real fixtures")
print(f"+ {has_replacement}  postponed originals that are now duplicates (original kept in list)")
print(f"= {380 + has_replacement} total API entries  (actual CSV has {len(rows)})")
print()
print(f"For own goals, this doesn't matter — we only process 'closed' matches.")
