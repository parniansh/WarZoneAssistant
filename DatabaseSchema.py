import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "warzone.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS conflict_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id        TEXT NOT NULL,
            source          TEXT NOT NULL,
            event_type      TEXT,
            country         TEXT,
            region          TEXT,
            latitude        REAL NOT NULL,
            longitude       REAL NOT NULL,
            timestamp       TEXT NOT NULL,
            fetched_at      TEXT NOT NULL,
            severity        TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low')),
            description     TEXT,
            is_active       INTEGER DEFAULT 1,
            UNIQUE(event_id, source)
        );

        CREATE TABLE IF NOT EXISTS fetch_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at      TEXT NOT NULL,
            source          TEXT NOT NULL,
            events_added    INTEGER DEFAULT 0,
            status          TEXT CHECK(status IN ('success', 'fail')),
            error_message   TEXT
        );

        CREATE TABLE IF NOT EXISTS static_resources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            osm_id          TEXT NOT NULL,  --OpenStreetMap ID to avoid duplicates
            resource_type   TEXT NOT NULL,
            name            TEXT,
            country         TEXT,
            region          TEXT,
            latitude        REAL NOT NULL,
            longitude       REAL NOT NULL,
            address         TEXT,
            phone           TEXT,
            fetched_at      TEXT NOT NULL,
            UNIQUE(osm_id, resource_type)
        );

        CREATE TABLE IF NOT EXISTS dynamic_resources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id     TEXT NOT NULL,
            source          TEXT NOT NULL,
            resource_type   TEXT NOT NULL,
            name            TEXT,
            country         TEXT,
            region          TEXT,
            latitude        REAL NOT NULL,
            longitude       REAL NOT NULL,
            description     TEXT,
            valid_from      TEXT,
            valid_until     TEXT,
            fetched_at      TEXT NOT NULL,
            is_active       INTEGER DEFAULT 1,
            UNIQUE(resource_id, source)
        );

        CREATE INDEX IF NOT EXISTS idx_conflict_location
            ON conflict_events (latitude, longitude);

        CREATE INDEX IF NOT EXISTS idx_conflict_active
            ON conflict_events (is_active, timestamp);

        CREATE INDEX IF NOT EXISTS idx_conflict_country
            ON conflict_events (country);

        CREATE INDEX IF NOT EXISTS idx_static_location
            ON static_resources (latitude, longitude);

        CREATE INDEX IF NOT EXISTS idx_static_country
            ON static_resources (country, resource_type);

        CREATE INDEX IF NOT EXISTS idx_dynamic_location
            ON dynamic_resources (latitude, longitude);

        CREATE INDEX IF NOT EXISTS idx_dynamic_active
            ON dynamic_resources (is_active, country);
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()