-- EPL Own Goals 25/26 — Supabase schema
-- Run this migration once (via Supabase MCP apply_migration or SQL Editor).

-- Seasons (one row per season; supports future seasons)
create table if not exists public.seasons (
  id uuid primary key default gen_random_uuid(),
  sportradar_season_id text not null unique,
  competition_id text not null,
  name text not null,
  created_at timestamptz not null default now()
);

-- Schedule: one row per match per season (upsert by sport_event_id)
create table if not exists public.schedule (
  id uuid primary key default gen_random_uuid(),
  season_id uuid not null references public.seasons(id) on delete cascade,
  sport_event_id text not null,
  start_time timestamptz,
  round text,
  home_team text,
  home_team_id text,
  away_team text,
  away_team_id text,
  status text,
  match_status text,
  home_score int,
  away_score int,
  updated_at timestamptz not null default now(),
  unique(season_id, sport_event_id)
);

create index if not exists idx_schedule_season_id on public.schedule(season_id);
create index if not exists idx_schedule_status on public.schedule(status);
create index if not exists idx_schedule_sport_event_id on public.schedule(sport_event_id);

-- Timelines: which matches have had their timeline fetched (avoids re-fetching)
-- Optional: store raw JSON here to avoid filesystem; or leave null and keep data/timelines/*.json
create table if not exists public.match_timelines (
  id uuid primary key default gen_random_uuid(),
  schedule_id uuid not null references public.schedule(id) on delete cascade unique,
  fetched_at timestamptz not null default now(),
  timeline_json jsonb
);

create index if not exists idx_match_timelines_schedule_id on public.match_timelines(schedule_id);

-- Own goals (extracted from timelines)
create table if not exists public.own_goals (
  id uuid primary key default gen_random_uuid(),
  sport_event_id text not null,
  match_date date,
  round text,
  home_team text,
  away_team text,
  og_player text,
  og_player_id text,
  og_player_team text,
  benefiting_team text,
  minute text,
  stoppage_time text,
  home_score_after int,
  away_score_after int,
  final_home_score int,
  final_away_score int,
  commentary text,
  created_at timestamptz not null default now()
);

create index if not exists idx_own_goals_sport_event_id on public.own_goals(sport_event_id);
create index if not exists idx_own_goals_match_date on public.own_goals(match_date);

-- Optional: RLS (enable if you add auth later)
-- alter table public.seasons enable row level security;
-- alter table public.schedule enable row level security;
-- alter table public.match_timelines enable row level security;
-- alter table public.own_goals enable row level security;
