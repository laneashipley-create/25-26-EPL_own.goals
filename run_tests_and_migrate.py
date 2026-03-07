"""
Run connection test, then migrate CSV to Supabase, then full pipeline.

Usage: python run_tests_and_migrate.py

Run from a terminal where Python is available (e.g. after activating venv).
"""

import subprocess
import sys


def run(name: str, *args: str) -> bool:
    cmd = [sys.executable, *args]
    print(f"\n{'='*60}\n  {name}\n{'='*60}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"\nExiting after failure: {name}")
        sys.exit(r.returncode)
    return True


def main():
    run("1. Test Supabase connection", "test_supabase.py")
    run("2. Migrate CSV to Supabase", "migrate_csv_to_supabase.py")
    run("3. Full pipeline (schedule → timelines → own goals → report)", "run_all.py")
    print("\nAll steps completed.")


if __name__ == "__main__":
    main()
