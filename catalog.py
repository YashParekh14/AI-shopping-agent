"""
Catalog domain logic: product search, lookup, and order creation.

search_products now joins ratings directly so the agent gets everything
it needs in a single tool call — no separate get_ratings step required.
"""

from typing import Optional

from db import get_connection


def search_products(
    query: str = "",
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
    min_rating: Optional[float] = None,
) -> list[dict]:
    """Search products, joining average ratings from the reviews table.

    Returns products with their average_rating and review_count included,
    so the agent never needs a separate ratings call.
    """
    sql = """
        SELECT p.id, p.name, p.category, p.price, p.description, p.is_organic,
               ROUND(COALESCE(AVG(r.rating), 0), 2) AS average_rating,
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

    sql += " GROUP BY p.id"

    if min_rating is not None:
        sql += " HAVING average_rating >= ?"
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
            "average_rating": row["average_rating"],
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
            (product_id,),
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
    """Create an order for a product. Returns a result dict.

    On success: {"ok": True, "order_id", "product_name", "price"}
    On unknown product: {"ok": False, "error": "..."}
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT name, price FROM products WHERE id = ?", (product_id,)
        ).fetchone()

        if row is None:
            return {"ok": False, "error": f"product with ID {product_id} not found"}

        cursor = conn.execute(
            "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
            (product_id, row["name"], row["price"]),
        )
        return {
            "ok": True,
            "order_id": cursor.lastrowid,
            "product_name": row["name"],
            "price": row["price"],
        }
