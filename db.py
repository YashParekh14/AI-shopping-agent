
import sqlite3
from contextlib import contextmanager

import config


@contextmanager
def get_connection(db_path: str | None = None):
    
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
