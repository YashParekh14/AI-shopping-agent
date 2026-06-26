
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


def test_search_results_sorted_by_price_ascending(test_db):
    results = catalog.search_products(query="honey")
    prices = [p["price"] for p in results]
    assert prices == sorted(prices)


def test_search_empty_query_matches_by_category(test_db):
    results = catalog.search_products(query="oil")
    assert {p["name"] for p in results} == {"Coconut Oil"}


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
    # confirm nothing was written
    import sqlite3
    conn = sqlite3.connect(test_db)
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    assert count == 0
