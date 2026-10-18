"""The single SQLAlchemy object shared by all models."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign keys unless this pragma is turned on for each connection."""
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def utcnow():
    """Current UTC time without tzinfo (SQLite does not store time zones)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(value):
    """Datetime -> ISO string for JSON responses (None stays None)."""
    return value.isoformat(timespec="seconds") + "Z" if value else None
