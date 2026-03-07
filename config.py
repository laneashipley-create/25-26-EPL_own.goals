"""
Central configuration for the EPL Own Goals project.
"""

import os

# API key: env var for CI, or config_local.py for local dev (gitignored)
try:
    from config_local import API_KEY as _LOCAL_KEY
    API_KEY = _LOCAL_KEY
except ImportError:
    API_KEY = os.environ.get("SPORTRADAR_API_KEY", "")
BASE_URL = "https://api.sportradar.com/soccer/trial/v4/en"

COMPETITION_ID = "sr:competition:17"   # English Premier League
SEASON_ID = "sr:season:130281"         # 2025/26 season (confirmed)
SEASON_NAME = "Premier League 25/26"

# Output files
SCHEDULE_CSV = "data/schedule.csv"
OWN_GOALS_CSV = "data/own_goals.csv"
TIMELINES_DIR = "data/timelines"       # cached raw JSON responses
REPORT_HTML = "report.html"

# Rate limiting: Sportradar trial keys are limited to 1 request/second
REQUEST_DELAY_SECONDS = 1.1

# Only fetch timelines for matches with these statuses
COMPLETED_STATUSES = {"closed", "ended"}

# Supabase — EPL Own Goals project (key from config_local or env)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yoesorfzvtbdmvrdtqoo.supabase.co")
try:
    from config_local import SUPABASE_KEY as _LOCAL_SUPABASE_KEY
    SUPABASE_KEY = _LOCAL_SUPABASE_KEY
except (ImportError, AttributeError):
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_ANON_KEY", "")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
