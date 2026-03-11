"""
Build an HTML snippet describing own goals added since the previous report.

Usage:
  python build_email_summary.py previous.csv current.csv output.html
"""

from __future__ import annotations

import csv
import html
import os
import sys


def load_rows(path: str) -> list[dict]:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def row_key(row: dict) -> tuple:
    return (
        row.get("sport_event_id", ""),
        row.get("og_player_id", ""),
        row.get("minute", ""),
        row.get("stoppage_time", ""),
        row.get("home_score_after", ""),
        row.get("away_score_after", ""),
    )


def format_minute(row: dict) -> str:
    minute = row.get("minute", "")
    stoppage = row.get("stoppage_time", "")
    if not minute:
        return "—"
    if stoppage:
        return f"{minute}+{stoppage}'"
    return f"{minute}'"


def display_name(raw: str) -> str:
    if ", " in raw:
        last, first = raw.split(", ", 1)
        return f"{first} {last}"
    return raw


def build_summary(previous_rows: list[dict], current_rows: list[dict]) -> str:
    previous_keys = {row_key(row) for row in previous_rows}
    new_rows = [row for row in current_rows if row_key(row) not in previous_keys]

    if not previous_rows:
        return (
            "<p>This is the first saved report snapshot for this workflow, "
            "so there is no prior-week comparison yet.</p>"
        )

    if not new_rows:
        return "<p><strong>No new own goals</strong> since the last report.</p>"

    count = len(new_rows)
    intro = (
        f"<p><strong>Since the last report, there "
        f"{'has' if count == 1 else 'have'} been {count} new own goal"
        f"{'' if count == 1 else 's'}.</strong></p>"
    )

    items = []
    for row in new_rows:
        match_label = f"{row.get('home_team', '')} vs {row.get('away_team', '')}"
        scorer = display_name(row.get("og_player", "Unknown"))
        minute = format_minute(row)
        benefiting = row.get("benefiting_team", "")
        commentary = row.get("commentary", "")
        items.append(
            "<li>"
            f"<strong>{html.escape(match_label)}</strong> "
            f"({html.escape(row.get('match_date', ''))})"
            f"<br>Own goal scorer: {html.escape(scorer)}"
            f"<br>Minute: {html.escape(minute)}"
            f"<br>Benefited team: {html.escape(benefiting)}"
            + (
                f"<br>Commentary: <em>{html.escape(commentary)}</em>"
                if commentary
                else ""
            )
            + "</li>"
        )

    return intro + "<ul>" + "".join(items) + "</ul>"


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python build_email_summary.py previous.csv current.csv output.html")
        return 1

    previous_path, current_path, output_path = sys.argv[1:4]
    previous_rows = load_rows(previous_path)
    current_rows = load_rows(current_path)
    summary_html = build_summary(previous_rows, current_rows)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary_html)

    print(f"Wrote email summary to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
