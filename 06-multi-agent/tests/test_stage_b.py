import pytest

from router import classify_query


@pytest.mark.parametrize("query,route", [
    ("history for user_123", "record"),
    ("general guideline", "guideline"),
    ("doctor directory", "doctor"),
    ("weather today", "refuse"),
])
def test_four_way_router(query, route):
    assert classify_query(query) == route
