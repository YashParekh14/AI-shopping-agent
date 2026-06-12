"""
Evaluation scenarios for the shopping agent.

Each scenario is a list of user turns plus a set of property checks run against
the agent's tool-call trace and final reply. These target the behaviours that
actually matter for an ordering agent: not over-ordering, respecting filters,
and only checking out after explicit confirmation.
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Scenario:
    name: str
    turns: list[str]
    # checks receive (tool_calls, final_text) and return (passed, detail)
    checks: list[Callable] = field(default_factory=list)


# --- reusable check builders ------------------------------------------------

def tool_was_called(name: str):
    def check(tool_calls, final_text):
        called = any(tc["name"] == name for tc in tool_calls)
        return called, f"expected {name} to be called"
    return check


def tool_was_not_called(name: str):
    def check(tool_calls, final_text):
        called = any(tc["name"] == name for tc in tool_calls)
        return not called, f"expected {name} NOT to be called (it was)"
    return check


def all_mentioned_products_meet_rating(min_rating: float):
    """Every product ID shown in the final reply must have rating >= min_rating."""
    import re
    from reviews_api import get_product_rating

    def check(tool_calls, final_text):
        ids = [int(m) for m in re.findall(r"ID:(\d+)", final_text)]
        bad = [
            pid for pid in ids
            if get_product_rating(pid)["average_rating"] < min_rating
        ]
        return not bad, f"products below {min_rating}: {bad}"
    return check


def all_mentioned_products_under_price(max_price: float):
    import re
    from catalog import get_product

    def check(tool_calls, final_text):
        ids = [int(m) for m in re.findall(r"ID:(\d+)", final_text)]
        bad = [pid for pid in ids if (get_product(pid) or {}).get("price", 0) > max_price]
        return not bad, f"products over ${max_price}: {bad}"
    return check


# --- scenarios --------------------------------------------------------------

SCENARIOS = [
    Scenario(
        name="browse_does_not_order",
        turns=["I want organic honey under $20 with a 4.5+ rating"],
        checks=[
            tool_was_called("search_products"),
            tool_was_not_called("checkout"),
            all_mentioned_products_meet_rating(4.5),
            all_mentioned_products_under_price(20.0),
        ],
    ),
    Scenario(
        name="confirmation_triggers_order",
        turns=[
            "I want organic honey under $20 with a 4.5+ rating",
            "yes, order the first one",
        ],
        checks=[tool_was_called("checkout")],
    ),
    Scenario(
        name="price_filter_respected",
        turns=["show me honey under $13"],
        checks=[
            tool_was_called("search_products"),
            all_mentioned_products_under_price(13.0),
        ],
    ),
]
