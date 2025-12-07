#!/usr/bin/env bash
set -euo pipefail

# Helper to apply DB migration 001_fix_schema.sql
# Usage: DATABASE_URL=postgres://user:pass@host:port/dbname ./scripts/apply_migration.sh

if [ -z "${DATABASE_URL-}" ]; then
  echo "ERROR: DATABASE_URL is not set. Export it and retry."
  echo "Example: export DATABASE_URL=\"postgres://user:pass@host:5432/dbname\""
  exit 2
fi

MIGRATION_FILE="db/migrations/001_fix_schema.sql"
if [ ! -f "${MIGRATION_FILE}" ]; then
  echo "ERROR: Migration file ${MIGRATION_FILE} not found." >&2
  exit 3
fi

echo "Applying migration ${MIGRATION_FILE} to database..."
psql "$DATABASE_URL" -f "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
  echo "Migration applied successfully."
else
  echo "Migration failed. Check psql output above for errors." >&2
  exit 4
fi
