"""
Catalog domain logic: product search, lookup, and order creation.

These are plain functions with no LLM / LangChain dependency, which keeps the
business logic unit-testable in isolation. The agent's @tool functions in
shopping_agent.py are thin wrappers around these.
"""

from typing import Optional

from db import get_connection


def search_products(
    query: str = "",
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
) -> list[dict]:
    """Search products by keyword (name/description/category), with optional
    max_price and organic filters. Returns a list of product dicts."""
    sql = (
        "SELECT id, name, category, price, description, is_organic "
        "FROM products WHERE 1=1"
    )
    params: list = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    if is_organic is not None:
        sql += " AND is_organic = ?"
        params.append(1 if is_organic else 0)

    sql += " ORDER BY price ASC"

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
        }
        for row in rows
    ]


def get_product(product_id: int) -> Optional[dict]:
    """Return a single product dict by ID, or None if it doesn't exist."""
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
    On unknown product: {"ok": False, "error": "..."}.

    Validation happens here in code rather than relying solely on the agent's
    prompt, so an invalid product_id can never reach the orders table.
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
