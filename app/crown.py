"""Crown (Коронный) recipe formula.

From spec §7.5:

  1. Walk the user's history (successful order/mix only).
  2. For each entry, count occurrences of: джин, кола, молоко, сок (these four only).
  3. X = ingredient with the maximum counter.
  4. Tie-break: джин > кола > молоко > сок.
  5. Fresh state → tie-break wins → джин.

Crown recipe = [лёд, водка, X].
"""
from __future__ import annotations

from app.drinks import drink_ingredients


CROWN_TRACKED: tuple[str, ...] = ("джин", "кола", "молоко", "сок")
CROWN_TIE_BREAK: list[str] = ["джин", "кола", "молоко", "сок"]


def crown_third_ingredient(history: list) -> str:
    counts = dict.fromkeys(CROWN_TRACKED, 0)
    for entry in history:
        drink_name = getattr(entry, "drink", None) if not isinstance(entry, dict) else entry.get("drink")
        if not drink_name:
            continue
        for ing in drink_ingredients(drink_name):
            if ing in counts:
                counts[ing] += 1
    # Sort by (count desc, tiebreak position asc).
    return sorted(CROWN_TIE_BREAK, key=lambda k: (-counts[k], CROWN_TIE_BREAK.index(k)))[0]


def crown_recipe(history: list) -> list[str]:
    return ["лёд", "водка", crown_third_ingredient(history)]
