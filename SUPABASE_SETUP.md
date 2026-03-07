# Supabase setup for EPL Own Goals 25/26

## MCP access

**You already have access.** The project’s `mcps` folder (under `.cursor/projects/...`) contains the Supabase MCP and other user MCPs. You do **not** need to copy a master MCP file from `C:\Users\l.shipley\.cursor` into this project.

- **Supabase MCP** is available as `user-supabase` and exposes tools such as:
  - `execute_sql`, `apply_migration`, `list_tables`, `list_migrations`, `create_branch`, etc.
- All Supabase tools take a **`project_id`** argument. That value comes from **linking your Supabase project in Cursor** (e.g. Cursor Settings → Supabase → Link project). Once linked, the agent can use `project_id` when calling these tools.

## Applying the schema

1. **Link your Supabase project in Cursor** (if not already) so `project_id` is available.
2. Apply the migration either:
   - **Via MCP (agent):** ask the agent to run `apply_migration` with:
     - `project_id`: your linked project ref
     - `name`: `epl_own_goals_schema`
     - `query`: contents of `supabase/migrations/20250306000000_epl_own_goals_schema.sql`
   - **Manually:** open the [Supabase SQL Editor](https://supabase.com/dashboard), create a new project if needed, then paste and run the SQL from that file.

## Runtime (script) — reducing run time

The pipeline will be updated to:

1. **Seasons** — Ensure the 25/26 season exists in `public.seasons` (by `sportradar_season_id`).
2. **Schedule** — Fetch schedule from Sportradar, then **upsert** into `public.schedule` so we don’t re-fetch from scratch every time; only refresh when you run step 2.
3. **Timelines** — For completed matches, only fetch timelines for matches that **don’t** have a row in `public.match_timelines` (or that don’t have a cached file). That way the script doesn’t start from the beginning of the season each run.
4. **Own goals** — Upsert into `public.own_goals` from the timeline data; report can read from DB (or from CSV if you keep a CSV export step).

To do this from Python, the script will use the **Supabase client** with credentials from the environment (not the MCP, which is for Cursor/agent use). Add to `.env` or `config_local.py` (gitignored):

- `SUPABASE_URL` — project URL (e.g. `https://xxxx.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY` — for server-side or anon access

Then install and use:

```bash
pip install supabase
```

The next step is to add Supabase URL/key to `config.py` and implement the DB-backed versions of step 2, 3, and 4 (and optionally the report from DB).
