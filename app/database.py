import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL, avatar TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
  target_cents INTEGER NOT NULL CHECK(target_cents>0), target_date TEXT, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS contributions(id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL CHECK(amount_cents>0), note TEXT, day TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS quest_claims(quest_id TEXT PRIMARY KEY, claimed_on TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS daily_claims(day TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


def default_db_path() -> str:
    # PENNYQUEST_DB lets a host point at a persistent volume (e.g. /data/pennyquest.db).
    return os.environ.get("PENNYQUEST_DB") or os.path.join(os.path.expanduser("~"), ".pennyquest", "pennyquest.db")


def connect(path: str | None = None) -> sqlite3.Connection:
    path = path or default_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR IGNORE INTO profile(id,name,avatar) VALUES(1,'Saver','🦊')")
    conn.commit()
    return conn
