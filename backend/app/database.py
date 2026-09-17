"""SQLite connection and schema setup for IssuePilot."""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "issuepilot.db"
load_dotenv(PROJECT_ROOT / ".env")


def get_database_path() -> Path:
    """Return the configured database path, anchored to the repository root."""

    configured_path = os.getenv("DATABASE_PATH")
    if not configured_path:
        return DEFAULT_DATABASE_PATH

    path = Path(configured_path).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Open a row-oriented SQLite connection and always close it."""

    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    # SQLite ignores REFERENCES clauses unless this is set per connection.
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the MVP schema when it does not exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY,
                conversation_id INTEGER NOT NULL
                    REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation
            ON chat_messages (conversation_id, id)
            """
        )
        connection.commit()
