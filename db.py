"""
Database connection helper.

Supports two backends controlled by the DATABASE_URL environment variable:

  DATABASE_URL not set  →  SQLite  (local dev, zero setup)
  DATABASE_URL set      →  PostgreSQL via psycopg2  (Supabase / AWS RDS)

A single get_connection() context manager handles both, so no other file
needs to know which backend is active. Commits on success, rolls back on
error, always closes.

SQL dialect note: both SQLite and PostgreSQL support standard SQL for our
queries. The only difference is the placeholder style:
  SQLite     →  ?
  PostgreSQL →  %s
get_connection() exposes a .execute() method that accepts both styles by
normalising ? → %s when using PostgreSQL.
"""

import sqlite3
from contextlib import contextmanager

import config


class _PgConnection:
    """Thin wrapper around a psycopg2 connection that normalises ? → %s
    so catalog.py can use the same SQL regardless of backend."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=None):
        sql = sql.replace("?", "%s")
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        return _PgCursor(cur)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


class _PgCursor:
    """Wraps psycopg2 cursor rows as dicts so callers can use row['column']
    the same way they would with sqlite3.Row."""

    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in self._cur.description]
        return dict(zip(cols, row))

    def fetchall(self):
        cols = [d[0] for d in self._cur.description]
        return [dict(zip(cols, row)) for row in self._cur.fetchall()]

    @property
    def lastrowid(self):
        # PostgreSQL uses RETURNING; psycopg2 puts it in fetchone()
        row = self._cur.fetchone()
        if row:
            return list(row.values())[0] if isinstance(row, dict) else row[0]
        return None


@contextmanager
def get_connection(db_path: str | None = None):
    """Yield a connection object, committing on success and always closing.

    Usage is identical regardless of backend:

        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM products WHERE id = ?", [1]).fetchall()
    """
    database_url = config.DATABASE_URL

    if database_url:
        # ── PostgreSQL / Supabase ──────────────────────────────────────
        import psycopg2
        conn = psycopg2.connect(database_url)
        wrapped = _PgConnection(conn)
        try:
            yield wrapped
            wrapped.commit()
        except Exception:
            wrapped.rollback()
            raise
        finally:
            wrapped.close()
    else:
        # ── SQLite (local dev fallback) ────────────────────────────────
        path = db_path if db_path is not None else config.DB_PATH
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
