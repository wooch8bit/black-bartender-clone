"""Repeat-cycle mechanics for /order and /mix.

Probed sequence on a fresh token ordering KL repeatedly:

  #1 → ok, price 15, no flag.
  #2 → ok, price 15, no flag.
  #3 → ok, price 15, no flag.   AFTER this success: profile.favorite_drink = "Куба Либре".
  #4 → ok, price 12, favorite:true.
  #5 → prompt:"repeat_check"  (no debit, no history, no mood movement, no counter increment).
  #6 → ok, price 12, favorite:true.
  #7 → ok, price 12, favorite:true.
  #8 → ok, price 0, free_every_7th:true.   This is the 7th *successful* repeat → free.
  #9 → ok, price 15 (full), no favorite flag.   Cycle reset after free_every_7th.

Model:

  • per-drink `repeat_counters[drink]` increments by 1 on every paid success.
  • when a drink hits 3 consecutive successes, set favorite_drink (if not already).
  • when about to land on the 5th consecutive success of the favorite, return the prompt instead
    (no debit, counter unchanged), and set pending_repeat_check.
  • on the next call after a prompt, if drink == pending → clear flag and proceed normally.
  • when the drink's counter would become 7, charge price 0 and emit free_every_7th:true,
    then reset that counter to 0 (cycle restart).
  • favorite:true + discount price are emitted while counter ∈ {4, 5, 6} of the cycle.
"""
from __future__ import annotations

from app.state import BarState


def maybe_set_favorite(state: BarState, drink: str) -> None:
    if state.favorite_drink is None and state.repeat_counters.get(drink, 0) >= 3:
        state.favorite_drink = drink


def should_prompt(state: BarState, drink: str) -> bool:
    """Return True if the next attempt should yield a repeat_check prompt."""
    if state.pending_repeat_check == drink:
        return False
    if state.favorite_drink != drink:
        return False
    return state.repeat_counters.get(drink, 0) == 4


def is_seventh(state: BarState, drink: str) -> bool:
    """The next paid increment would land on the 7th of this drink's cycle."""
    return state.repeat_counters.get(drink, 0) == 6


def in_favorite_window(state: BarState, drink: str) -> bool:
    """Whether the response should carry favorite:true and discounted price."""
    if state.favorite_drink != drink:
        return False
    c = state.repeat_counters.get(drink, 0)
    return 4 <= c <= 6
