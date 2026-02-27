"""
Master runner — executes all steps in order:
  Step 2: Fetch schedule → data/schedule.csv
  Step 3: Fetch timelines → data/timelines/*.json
  Step 4: Extract own goals → data/own_goals.csv
  Step 5: Generate report → report.html

Safe to re-run: timelines are cached, so only new/missing ones are fetched.
"""

import step2_get_schedule
import step3_fetch_timelines
import step4_extract_own_goals
import generate_report

DIVIDER = "─" * 60

def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

if __name__ == "__main__":
    section("STEP 2 — Fetching schedule")
    step2_get_schedule.main()

    section("STEP 3 — Fetching timelines (cached)")
    step3_fetch_timelines.main()

    section("STEP 4 — Extracting own goals")
    step4_extract_own_goals.main()

    section("STEP 5 — Generating HTML report")
    generate_report.main()

    print(f"\n{DIVIDER}")
    print("  All done! Open report.html in your browser.")
    print(DIVIDER)
