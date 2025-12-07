-- 001_fix_schema.sql
-- SQL migration helper for PostgreSQL to add missing columns and rename reserved column
-- Run with: psql "$DATABASE_URL" -f db/migrations/001_fix_schema.sql

-- 1) Add missing User columns if not exists
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;

-- preferences: add JSONB column if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'preferences'
    ) THEN
        ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}'::jsonb;
    END IF;
END$$;

-- 2) Rename metadata -> metadata_json in proprietes_consolidees if needed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'proprietes_consolidees' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE proprietes_consolidees RENAME COLUMN metadata TO metadata_json;
    END IF;
END$$;

-- 3) If you added new columns and want to backfill defaults for existing rows you can run updates
-- Example: set preferences to empty object where NULL
UPDATE users SET preferences = '{}'::jsonb WHERE preferences IS NULL;

-- 4) Optional: ensure `is_verified` exists for all users
UPDATE users SET is_verified = FALSE WHERE is_verified IS NULL;

-- 5) Commit is implicit for psql script run; if running inside a transaction rollbacks may be required after errors.

-- End of script
