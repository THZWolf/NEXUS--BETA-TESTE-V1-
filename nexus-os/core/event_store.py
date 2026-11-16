"""Shared SQLite event store for the local API and offline importer."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DATA_DIR = Path(os.environ.get("NEXUS_DATA_DIR", "/var/lib/nexus-os"))
DATABASE = DATA_DIR / "events.sqlite3"
_initialized = False
_initialization_lock = threading.Lock()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(mode=0o750, parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    global _initialized
    with _initialization_lock:
        if _initialized:
            return
        with connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS events_created_at_idx ON events(created_at)"
            )
        _initialized = True


def record_event(event_type: str, payload: dict[str, str]) -> int:
    initialize_database()
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO events(event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload, ensure_ascii=True), int(time.time())),
        )
        return int(cursor.lastrowid)


def events_after(after: int = 0, limit: int = 100) -> list[dict[str, object]]:
    bounded_limit = max(1, min(limit, 500))
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, event_type, payload, created_at
            FROM events WHERE id > ? ORDER BY id LIMIT ?
            """,
            (max(0, after), bounded_limit),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "event_type": row["event_type"],
            "payload": json.loads(row["payload"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
