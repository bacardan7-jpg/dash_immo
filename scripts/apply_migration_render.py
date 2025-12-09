#!/usr/bin/env python3
"""Run DB migration file in environments that may not have `psql`.

Usage on Render (open Shell for your Web Service in Render):
  python3 scripts/apply_migration_render.py

It uses the `DATABASE_URL` environment variable provided by Render.
"""
import os
import sys
import pathlib
import psycopg2


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        print("On Render the variable is set in Environment > Environment Variables for the service.")
        sys.exit(2)

    migration_path = pathlib.Path(__file__).resolve().parents[1] / 'db' / 'migrations' / '001_fix_schema.sql'
    if not migration_path.exists():
        print(f"ERROR: migration file not found: {migration_path}")
        sys.exit(3)

    sql = migration_path.read_text()

    try:
        conn = psycopg2.connect(database_url)
        # Run each top-level statement in autocommit so we don't inherit aborted transactions
        conn.autocommit = True
        cur = conn.cursor()
        print(f"Applying migration: {migration_path}")
        cur.execute(sql)
        cur.close()
        conn.close()
        print("Migration applied successfully.")
    except Exception as e:
        print("Migration failed:", e)
        sys.exit(4)


if __name__ == '__main__':
    main()
