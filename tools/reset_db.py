"""Rebuild the database from the SQL files (users, schema, sample data, views).

    python tools/reset_db.py

Uses the `mysql` command-line client with an administrator account.
Set PARKING_ADMIN_ARGS if yours is not "-u root", for example:
    PARKING_ADMIN_ARGS="-u root -pYourPassword"
"""
import os
import shlex
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL = os.path.join(ROOT, "sql")
STEPS = [("00_create_app_user.sql", None), ("01_schema.sql", None),
         ("02_sample_data.sql", "smart_parking"), ("03_views.sql", "smart_parking")]


def reset():
    admin = shlex.split(os.getenv("PARKING_ADMIN_ARGS", "-u root"))
    for filename, database in STEPS:
        cmd = ["mysql"] + admin + ([database] if database else [])
        with open(os.path.join(SQL, filename), "rb") as fh:
            result = subprocess.run(cmd, stdin=fh, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"{filename} failed: {result.stderr.strip()}")


if __name__ == "__main__":
    try:
        reset()
        print("Database rebuilt: users, schema, sample data and views loaded.")
    except (RuntimeError, FileNotFoundError) as e:
        print("Could not rebuild the database:", e)
        sys.exit(1)
