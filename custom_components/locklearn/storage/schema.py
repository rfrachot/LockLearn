"""P0 SQLite schemas.

The complete V1 schemas are delivered in later phases. These tables are the
smallest persistent slice needed to prove concurrency, backup and session CAS.
"""

STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    track_id TEXT,
    status TEXT NOT NULL,
    version INTEGER NOT NULL,
    current_position INTEGER NOT NULL,
    started_at_utc TEXT NOT NULL,
    last_activity_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_profile_status_activity
ON sessions(profile_id, status, last_activity_at_utc);

CREATE TABLE IF NOT EXISTS session_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    answer_json TEXT NOT NULL,
    resulting_version INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    UNIQUE(session_id, resulting_version)
);

CREATE TABLE IF NOT EXISTS progress (
    profile_id TEXT NOT NULL,
    track_id TEXT NOT NULL,
    card_key TEXT NOT NULL,
    state TEXT NOT NULL,
    next_due_at_utc TEXT,
    PRIMARY KEY(profile_id, track_id, card_key)
);

CREATE INDEX IF NOT EXISTS progress_due
ON progress(profile_id, track_id, state, next_due_at_utc);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_user_id TEXT,
    profile_id TEXT,
    payload_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);
"""

CONTENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS card_definitions (
    card_key TEXT PRIMARY KEY,
    pack_version_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS card_definitions_pack
ON card_definitions(pack_version_id, ordinal);
"""
