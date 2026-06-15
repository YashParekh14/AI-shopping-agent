
from db import get_connection


def get_product_rating(product_id: int) -> dict:
    """Return average rating and review count for a single product."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT AVG(rating) AS avg, COUNT(*) AS cnt "
            "FROM reviews WHERE product_id = ?",
            (product_id,),
        ).fetchone()

    avg = round(row["avg"], 2) if row and row["avg"] is not None else 0.0
    count = row["cnt"] if row else 0
    return {"product_id": product_id, "average_rating": avg, "review_count": count}


def get_ratings_for_products(product_ids: list[int]) -> list[dict]:
    
    if not product_ids:
        return []

    placeholders = ",".join("?" * len(product_ids))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT product_id, AVG(rating) AS avg, COUNT(*) AS cnt
            FROM reviews
            WHERE product_id IN ({placeholders})
            GROUP BY product_id
            """,
            product_ids,
        ).fetchall()

    ratings_map = {
        r["product_id"]: {
            "average_rating": round(r["avg"], 2),
            "review_count": r["cnt"],
        }
        for r in rows
    }
    return [
        {
            "product_id": pid,
            "average_rating": ratings_map.get(pid, {}).get("average_rating", 0.0),
            "review_count": ratings_map.get(pid, {}).get("review_count", 0),
        }
        for pid in product_ids
    ]


if __name__ == "__main__":
    result = get_product_rating(1)
    print("Single product rating:")
    print(
        f"  Product {result['product_id']}: {result['average_rating']} stars "
        f"({result['review_count']} reviews)"
    )

    print("\nBatch ratings:")
    for r in get_ratings_for_products([1, 3, 5, 7]):
        print(
            f"  Product {r['product_id']}: {r['average_rating']} stars "
            f"({r['review_count']} reviews)"
        )
