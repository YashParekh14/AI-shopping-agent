"""
Shared fixtures. Builds a small, fully-controlled SQLite database in a temp
file so tests are deterministic and never touch the real store.db.
"""

import sqlite3

import pytest

import config


@pytest.fixture()
def test_db(tmp_path, monkeypatch):
    """Create an isolated DB and point config.DB_PATH at it."""
    db_path = tmp_path / "test_store.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY, name TEXT, category TEXT,
            price REAL, description TEXT, is_organic INTEGER DEFAULT 0
        );
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER, rating REAL, reviewer_name TEXT, review_text TEXT
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER, product_name TEXT, price REAL,
            ordered_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    products = [
        (1, "Organic Raw Honey", "honey", 14.99, "Pure organic raw honey", 1),
        (2, "Wildflower Honey", "honey", 12.99, "Natural wildflower honey", 0),
        (3, "Organic Manuka Honey", "honey", 29.99, "Premium organic Manuka", 1),
        (4, "Coconut Oil", "oil", 12.49, "Refined coconut oil", 0),
    ]
    cur.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)
    reviews = [
        (1, 5.0), (1, 4.0),        # product 1 avg 4.5
        (2, 3.0), (2, 4.0),        # product 2 avg 3.5
        (3, 5.0), (3, 5.0), (3, 4.0),  # product 3 avg ~4.67
        # product 4 has no reviews
    ]
    cur.executemany(
        "INSERT INTO reviews (product_id, rating) VALUES (?, ?)", reviews
    )
    conn.commit()
    conn.close()

    # Redirect every module that reads config.DB_PATH at call time.
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    return str(db_path)
