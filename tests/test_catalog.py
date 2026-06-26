"""Tests for the catalog domain logic (search, lookup, ordering)."""

import catalog


def test_search_returns_all_products_for_broad_query(test_db):
    results = catalog.search_products(query="honey")
    names = {p["name"] for p in results}
    assert names == {"Organic Raw Honey", "Wildflower Honey", "Organic Manuka Honey"}


def test_search_respects_max_price(test_db):
    results = catalog.search_products(query="honey", max_price=15.0)
    assert all(p["price"] <= 15.0 for p in results)
    assert "Organic Manuka Honey" not in {p["name"] for p in results}


def test_search_filters_organic(test_db):
    results = catalog.search_products(query="honey", is_organic=True)
    assert all(p["is_organic"] is True for p in results)
    assert {p["name"] for p in results} == {"Organic Raw Honey", "Organic Manuka Honey"}


def test_search_results_sorted_by_rating_then_price(test_db):
    """Results are sorted by average_rating DESC, then price ASC.
    In test data: Manuka(4.67) > Raw(4.5) > Wildflower(3.5)
    so Manuka comes first despite being most expensive.
    """
    results = catalog.search_products(query="honey")
    ratings = [p["average_rating"] for p in results]
    # Ratings should be descending
    assert ratings == sorted(ratings, reverse=True)


def test_search_results_include_ratings(test_db):
    """Every search result should include average_rating and review_count."""
    results = catalog.search_products(query="honey")
    for p in results:
        assert "average_rating" in p
        assert "review_count" in p


def test_search_empty_query_matches_by_category(test_db):
    results = catalog.search_products(query="oil")
    assert {p["name"] for p in results} == {"Coconut Oil"}


def test_search_min_rating_filter(test_db):
    """Only products with average_rating >= min_rating should be returned."""
    results = catalog.search_products(query="honey", min_rating=4.0)
    assert all(p["average_rating"] >= 4.0 for p in results)
    # Wildflower has 3.5 avg so should be excluded
    assert "Wildflower Honey" not in {p["name"] for p in results}


def test_get_product_returns_dict(test_db):
    product = catalog.get_product(1)
    assert product["name"] == "Organic Raw Honey"
    assert product["is_organic"] is True


def test_get_product_unknown_id_returns_none(test_db):
    assert catalog.get_product(9999) is None


def test_create_order_success(test_db):
    result = catalog.create_order(1)
    assert result["ok"] is True
    assert result["product_name"] == "Organic Raw Honey"
    assert result["price"] == 14.99
    assert isinstance(result["order_id"], int)


def test_create_order_unknown_product_does_not_insert(test_db):
    result = catalog.create_order(9999)
    assert result["ok"] is False
    assert "not found" in result["error"]
    import sqlite3
    conn = sqlite3.connect(test_db)
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    assert count == 0
