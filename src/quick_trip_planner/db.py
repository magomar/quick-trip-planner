"""SQLite database connection and schema management."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "trips.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS countries (
                code      TEXT PRIMARY KEY,
                name      TEXT NOT NULL,
                flag      TEXT NOT NULL,
                enabled   INTEGER NOT NULL DEFAULT 0,
                available INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS airports (
                iata         TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                city         TEXT NOT NULL,
                country_code TEXT NOT NULL REFERENCES countries(code),
                lat          REAL NOT NULL,
                lon          REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS routes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_iata TEXT NOT NULL REFERENCES airports(iata),
                dest_iata   TEXT NOT NULL REFERENCES airports(iata),
                days        TEXT NOT NULL DEFAULT '[]',
                has_am      INTEGER NOT NULL DEFAULT 0,
                has_pm      INTEGER NOT NULL DEFAULT 0,
                dep_am      TEXT,
                dep_pm      TEXT,
                ret_am      TEXT,
                ret_pm      TEXT,
                UNIQUE(origin_iata, dest_iata)
            );

            CREATE TABLE IF NOT EXISTS flights (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_iata TEXT NOT NULL REFERENCES airports(iata),
                dest_iata   TEXT NOT NULL REFERENCES airports(iata),
                flight_no   TEXT,
                airline     TEXT,
                dep_time    TEXT,
                ret_time    TEXT,
                days        TEXT NOT NULL DEFAULT '[]',
                UNIQUE(origin_iata, dest_iata, flight_no, dep_time)
            );

            CREATE INDEX IF NOT EXISTS idx_routes_origin ON routes(origin_iata);
            CREATE INDEX IF NOT EXISTS idx_flights_origin ON flights(origin_iata);
            CREATE INDEX IF NOT EXISTS idx_flights_origin_dest ON flights(origin_iata, dest_iata);
            CREATE INDEX IF NOT EXISTS idx_airports_country ON airports(country_code);
        """)
