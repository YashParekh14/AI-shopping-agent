"""
Catalog domain logic: product search, lookup, and order creation.

Pure functions with no LLM dependency — fully unit-testable.
search_products joins ratings so the agent gets everything in one call.

Works with both SQLite (? placeholders) and PostgreSQL (%s via db.py wrapper).
"""

from typing import Optional
from db import get_connection
import config


def search_products(
    query: str = "",
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
    min_rating: Optional[float] = None,
) -> list[dict]:
    """Search products, joining average ratings.

    Returns each product with average_rating and review_count so the agent
    never needs a separate ratings call.
    """
    sql = """
        SELECT p.id, p.name, p.category, p.price, p.description, p.is_organic,
               ROUND(CAST(COALESCE(AVG(r.rating), 0) AS NUMERIC), 2) AS average_rating,
               COUNT(r.id) AS review_count
        FROM products p
        LEFT JOIN reviews r ON r.product_id = p.id
        WHERE 1=1
    """
    params: list = []

    if query:
        sql += " AND (p.name LIKE ? OR p.description LIKE ? OR p.category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if max_price is not None:
        sql += " AND p.price <= ?"
        params.append(max_price)

    if is_organic is not None:
        sql += " AND p.is_organic = ?"
        params.append(1 if is_organic else 0)

    sql += " GROUP BY p.id, p.name, p.category, p.price, p.description, p.is_organic"

    if min_rating is not None:
        sql += " HAVING ROUND(CAST(COALESCE(AVG(r.rating), 0) AS NUMERIC), 2) >= ?"
        params.append(min_rating)

    sql += " ORDER BY average_rating DESC, p.price ASC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
            "description": row["description"],
            "is_organic": bool(row["is_organic"]),
            "average_rating": float(row["average_rating"]),
            "review_count": row["review_count"],
        }
        for row in rows
    ]


def get_product(product_id: int) -> Optional[dict]:
    """Return a single product dict by ID, or None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, category, price, description, is_organic "
            "FROM products WHERE id = ?",
            [product_id],
        ).fetchone()

    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "price": row["price"],
        "description": row["description"],
        "is_organic": bool(row["is_organic"]),
    }


def create_order(product_id: int) -> dict:
    """Create an order. Validates product exists before writing.

    Returns {"ok": True, ...} on success or {"ok": False, "error": ...}.
    Uses a single INSERT...RETURNING id that works on both PostgreSQL and
    SQLite (SQLite ignores RETURNING but we fall back to last_insert_rowid).
    """
    with get_connection() as conn:
        # Validate product exists first
        row = conn.execute(
            "SELECT name, price FROM products WHERE id = ?",
            [product_id],
        ).fetchone()

        if row is None:
            return {"ok": False, "error": f"product with ID {product_id} not found"}

        product_name = row["name"]
        price = row["price"]

        if config.DATABASE_URL:
            # PostgreSQL — use RETURNING to get the new id
            result_row = conn.execute(
                "INSERT INTO orders (product_id, product_name, price) "
                "VALUES (?, ?, ?) RETURNING id",
                [product_id, product_name, price],
            ).fetchone()
            order_id = result_row["id"] if result_row else None
        else:
            # SQLite — insert then get rowid
            conn.execute(
                "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
                [product_id, product_name, price],
            )
            order_id = conn.execute(
                "SELECT id FROM orders ORDER BY id DESC LIMIT 1"
            ).fetchone()["id"]

        return {
            "ok": True,
            "order_id": order_id,
            "product_name": product_name,
            "price": price,
        }
