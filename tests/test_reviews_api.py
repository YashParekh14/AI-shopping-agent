"""Tests for the reviews API (single and batch ratings)."""

import reviews_api


def test_single_rating_averages_correctly(test_db):
    result = reviews_api.get_product_rating(1)
    assert result["average_rating"] == 4.5
    assert result["review_count"] == 2


def test_single_rating_no_reviews_returns_zero(test_db):
    result = reviews_api.get_product_rating(4)
    assert result["average_rating"] == 0.0
    assert result["review_count"] == 0


def test_batch_ratings_returns_one_entry_per_id(test_db):
    results = reviews_api.get_ratings_for_products([1, 2, 3, 4])
    assert len(results) == 4
    by_id = {r["product_id"]: r for r in results}
    assert by_id[1]["average_rating"] == 4.5
    assert by_id[2]["average_rating"] == 3.5
    assert by_id[3]["average_rating"] == 4.67
    assert by_id[4]["average_rating"] == 0.0  # no reviews -> default


def test_batch_ratings_preserves_input_order(test_db):
    ids = [3, 1, 4, 2]
    results = reviews_api.get_ratings_for_products(ids)
    assert [r["product_id"] for r in results] == ids


def test_batch_ratings_empty_list(test_db):
    assert reviews_api.get_ratings_for_products([]) == []


def test_batch_matches_single_for_each_product(test_db):
    """The batch path and single path should agree."""
    for pid in (1, 2, 3, 4):
        single = reviews_api.get_product_rating(pid)
        batch = reviews_api.get_ratings_for_products([pid])[0]
        assert single["average_rating"] == batch["average_rating"]
        assert single["review_count"] == batch["review_count"]
