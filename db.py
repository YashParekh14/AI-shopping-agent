"""
Database helpers.

A single context manager that guarantees connections are committed on success,
rolled back on error, and always closed. This replaces the manual
connect()/close() pattern that leaked connections whenever an exception was
raised between the two calls.
"""

import sqlite3
from contextlib import contextmanager

import config


@contextmanager
def get_connection(db_path: str | None = None):
    """Yield a SQLite connection, committing on success and always closing.

    The path is resolved from config at call time (not bound as a default) so
    tests can redirect config.DB_PATH to a temporary database.
    Rows are returned as sqlite3.Row so callers can use column names.
    """
    if db_path is None:
        db_path = config.DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
