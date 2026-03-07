"""
Supabase helpers for EPL Own Goals pipeline.

Use when USE_SUPABASE is True in config. Provides:
  - get_client() — PostgREST client (avoids full supabase pkg + C++ deps)
  - get_or_create_season() — ensure season row exists
  - upsert_schedule() — upsert schedule rows
  - get_completed_matches_without_timeline() — for step 3
  - upsert_timeline() / get_timeline_json() — store or read timeline
  - upsert_own_goals() — write extracted own goals

Install: pip install postgrest httpx
Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY)
"""

from __future__ import annotations

from config import USE_SUPABASE, SUPABASE_URL, SUPABASE_KEY, SEASON_ID, COMPETITION_ID, SEASON_NAME

_client = None


def get_client():
    """Return PostgREST client for Supabase tables; raises if not configured."""
    if not USE_SUPABASE:
        raise RuntimeError("Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY.")
    global _client
    if _client is None:
        from postgrest import SyncPostgrestClient
        base = SUPABASE_URL.rstrip("/")
        if not base.endswith("/rest/v1"):
            base = f"{base}/rest/v1"
        _client = SyncPostgrestClient(
            base,
            schema="public",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
        )
    return _client


def get_or_create_season():
    """Ensure the current season exists in public.seasons; return its id (uuid)."""
    supabase = get_client()
    r = supabase.table("seasons").select("id").eq("sportradar_season_id", SEASON_ID).execute()
    if r.data and len(r.data) > 0:
        return r.data[0]["id"]
    ins = supabase.table("seasons").insert({
        "sportradar_season_id": SEASON_ID,
        "competition_id": COMPETITION_ID,
        "name": SEASON_NAME,
    }).execute()
    return ins.data[0]["id"]


def upsert_schedule(season_id: str, rows: list[dict]) -> None:
    """Upsert schedule rows for the given season_id. Each row must include sport_event_id and schedule fields."""
    if not rows:
        return
    supabase = get_client()
    for row in rows:
        payload = {
            "season_id": season_id,
            "sport_event_id": row["sport_event_id"],
            "start_time": row.get("start_time") or None,
            "round": row.get("round") or None,
            "home_team": row.get("home_team") or None,
            "home_team_id": row.get("home_team_id") or None,
            "away_team": row.get("away_team") or None,
            "away_team_id": row.get("away_team_id") or None,
            "status": row.get("status") or None,
            "match_status": row.get("match_status") or None,
            "home_score": _int_or_none(row.get("home_score")),
            "away_score": _int_or_none(row.get("away_score")),
        }
        supabase.table("schedule").upsert(
            payload,
            on_conflict="season_id,sport_event_id",
            ignore_duplicates=False,
        ).execute()


def get_completed_schedule_for_season(season_id: str) -> list[dict]:
    """Return schedule rows that are completed (status in closed/ended)."""
    supabase = get_client()
    r = supabase.table("schedule").select("*").eq("season_id", season_id).in_("status", ["closed", "ended"]).execute()
    return r.data or []


def get_schedule_ids_with_timeline(season_id: str) -> set[str]:
    """Return set of schedule.id (uuid) that already have a match_timelines row."""
    supabase = get_client()
    # Get schedule ids that have timelines
    sched = supabase.table("schedule").select("id").eq("season_id", season_id).execute()
    sched_ids = [x["id"] for x in (sched.data or [])]
    if not sched_ids:
        return set()
    tl = supabase.table("match_timelines").select("schedule_id").in_("schedule_id", sched_ids).execute()
    return {x["schedule_id"] for x in (tl.data or [])}


def get_completed_matches_without_timeline(season_id: str) -> list[dict]:
    """Return completed schedule rows that do not yet have a timeline. Use this in step 3 to only fetch missing."""
    completed = get_completed_schedule_for_season(season_id)
    with_timeline = get_schedule_ids_with_timeline(season_id)
    return [r for r in completed if r["id"] not in with_timeline]


def upsert_timeline(schedule_id: str, timeline_json: dict | None = None) -> None:
    """Record that we have fetched the timeline for this schedule row. Optionally store timeline_json."""
    supabase = get_client()
    supabase.table("match_timelines").upsert({
        "schedule_id": schedule_id,
        "timeline_json": timeline_json,
    }, on_conflict="schedule_id", ignore_duplicates=False).execute()


def get_timeline_json(schedule_id: str) -> dict | None:
    """Return stored timeline JSON for a schedule row, or None if not stored."""
    supabase = get_client()
    r = supabase.table("match_timelines").select("timeline_json").eq("schedule_id", schedule_id).execute()
    if r.data and len(r.data) > 0 and r.data[0].get("timeline_json"):
        return r.data[0]["timeline_json"]
    return None


def get_completed_matches_with_timelines(season_id: str) -> list[dict]:
    """Return completed schedule rows that have timelines, with timeline_json attached. For step4."""
    completed = get_completed_schedule_for_season(season_id)
    with_tl_ids = get_schedule_ids_with_timeline(season_id)
    result = []
    for row in completed:
        if row["id"] not in with_tl_ids:
            continue
        tl = get_timeline_json(row["id"])
        if tl:
            row_copy = dict(row)
            row_copy["timeline_json"] = tl
            result.append(row_copy)
    return result


def get_all_own_goals() -> list[dict]:
    """Return all own_goals rows for the report. Keys match CSV/legacy format."""
    supabase = get_client()
    r = supabase.table("own_goals").select("*").order("match_date").order("minute").execute()
    rows = r.data or []
    # Normalize for report: ensure string values where needed
    out = []
    for row in rows:
        out.append({
            "sport_event_id": row.get("sport_event_id", ""),
            "match_date": str(row.get("match_date") or "")[:10],
            "round": str(row.get("round") or ""),
            "home_team": str(row.get("home_team") or ""),
            "away_team": str(row.get("away_team") or ""),
            "og_player": str(row.get("og_player") or ""),
            "og_player_id": str(row.get("og_player_id") or ""),
            "og_player_team": str(row.get("og_player_team") or ""),
            "benefiting_team": str(row.get("benefiting_team") or ""),
            "minute": str(row.get("minute") or ""),
            "stoppage_time": str(row.get("stoppage_time") or ""),
            "home_score_after": row.get("home_score_after") if row.get("home_score_after") is not None else "",
            "away_score_after": row.get("away_score_after") if row.get("away_score_after") is not None else "",
            "final_home_score": row.get("final_home_score") if row.get("final_home_score") is not None else "",
            "final_away_score": row.get("final_away_score") if row.get("final_away_score") is not None else "",
            "commentary": str(row.get("commentary") or ""),
        })
    return out


def get_report_stats() -> tuple[int, int]:
    """Return (completed_matches, timeline_events) for the report."""
    supabase = get_client()
    tl = supabase.table("match_timelines").select("timeline_json").execute()
    rows = tl.data or []
    completed_matches = len(rows)
    timeline_events = 0
    for row in rows:
        data = row.get("timeline_json") or {}
        timeline_events += len(data.get("timeline", []))
    return completed_matches, timeline_events


def get_schedule_by_sport_event_id(season_id: str, sport_event_id: str) -> dict | None:
    """Return schedule row by sport_event_id, or None."""
    supabase = get_client()
    r = supabase.table("schedule").select("*").eq("season_id", season_id).eq("sport_event_id", sport_event_id).execute()
    if r.data and len(r.data) > 0:
        return r.data[0]
    return None


def clear_own_goals() -> None:
    """Delete all own_goals. Call before re-inserting to avoid duplicates on pipeline re-run."""
    supabase = get_client()
    r = supabase.table("own_goals").select("id").execute()
    ids = [x["id"] for x in (r.data or [])]
    if ids:
        supabase.table("own_goals").delete().in_("id", ids).execute()


def upsert_own_goals(rows: list[dict], replace: bool = True) -> None:
    """Insert own_goals rows. If replace=True, clears existing rows first to avoid duplicates on re-run."""
    supabase = get_client()
    if replace:
        clear_own_goals()
    if not rows:
        return
    for row in rows:
        payload = {
            "sport_event_id": row.get("sport_event_id", ""),
            "match_date": row.get("match_date"),
            "round": row.get("round"),
            "home_team": row.get("home_team"),
            "away_team": row.get("away_team"),
            "og_player": row.get("og_player"),
            "og_player_id": row.get("og_player_id"),
            "og_player_team": row.get("og_player_team"),
            "benefiting_team": row.get("benefiting_team"),
            "minute": row.get("minute"),
            "stoppage_time": row.get("stoppage_time"),
            "home_score_after": _int_or_none(row.get("home_score_after")),
            "away_score_after": _int_or_none(row.get("away_score_after")),
            "final_home_score": _int_or_none(row.get("final_home_score")),
            "final_away_score": _int_or_none(row.get("final_away_score")),
            "commentary": row.get("commentary"),
        }
        supabase.table("own_goals").insert(payload).execute()


def _int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
