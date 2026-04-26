"""Core business logic for /order and /mix that handles common book-keeping.

A successful drink (regular, secret, Воздух, Crown) goes through this code path so that
mood deltas, history, success_counter, repeat counters, and special flags are all kept in
sync.
"""
from __future__ import annotations

from app.drinks import sort_ingredients_ru
from app.effects import apply_secret_effect
from app.hints import hint_for
from app.mood import DELTA, UNKNOWN_RECIPE_DELTA, clamp_mood, delta_for, mood_level
from app.pricing import BASE_NORMAL_PRICE, favorite_price, price_for
from app.ranks import rank_for
from app.state import BarState, HistoryEntry


# Notes that piggy-back on drink responses depending on mood/balance.
FRIENDLY_ORDER_NOTE = "Знаешь, если смешать самому — сэкономишь."
GENEROUS_ORDER_NOTE_ALT = "Я сегодня добрый. Каждый третий — за счёт заведения."


def _ranks(state: BarState) -> str:
    return rank_for(len({h.drink for h in state.history}))


def is_refused(drink: str, level: str) -> bool:
    return level == "hostile" and drink in ("Белый русский", "Лонг-Айленд")


def serve_regular_drink(
    state: BarState,
    drink: str,
    *,
    method: str,
    is_crown: bool = False,
) -> dict:
    """Process a regular (non-secret) drink success, including repeats/favorite/free/hint mechanics.

    Caller is responsible for handling secret drinks, Воздух, refused, insufficient_funds, etc.
    Returns the response dict (without `status` — caller may prepend extras like `prompt`).
    """
    pre_counter = state.repeat_counters.get(drink, 0)
    pending_match = state.pending_repeat_check == drink
    is_favorite = state.favorite_drink == drink

    # repeat_check prompt: only if favorite, pre-counter == 4, and we don't have a pending flag
    if is_favorite and pre_counter == 4 and not pending_match:
        state.pending_repeat_check = drink
        # No debit, no history, no mood movement.
        return {
            "status": "prompt",
            "prompt": "repeat_check",
            "balance": state.balance,
            "mood_level": mood_level(state.mood_score),
        }

    if pending_match:
        state.pending_repeat_check = None

    level = mood_level(state.mood_score)
    rank = _ranks(state)

    # Determine the would-be price and whether free_every_7th / generous_free apply.
    free_every_7th = pre_counter == 6 and is_favorite  # the 7th paid repeat → free
    new_counter = pre_counter + 1
    in_fav_window = is_favorite and new_counter in (4, 5, 6)

    # Generous-free: every 3rd successful order/mix in generous is free.
    state_generous_counter = state.generous_counter
    generous_free = level == "generous" and (state_generous_counter + 1) % 3 == 0

    if free_every_7th:
        price = 0
    elif generous_free:
        price = 0
    elif in_fav_window:
        price = favorite_price(drink)
    else:
        price = price_for(drink, level, rank=rank, method=method)

    if state.balance < price and price > 0:
        return {
            "status": "error",
            "error": "insufficient_funds",
            "price": price,
            "balance": state.balance,
            "mood_level": level,
        }

    # Commit success.
    state.balance -= price
    # Mood
    state.mood_score = clamp_mood(state.mood_score + delta_for(drink, level))
    state.history.append(HistoryEntry(drink=drink, price=price, method=method))

    # Update repeat counters
    if free_every_7th:
        state.repeat_counters[drink] = 0  # reset cycle after free
    else:
        state.repeat_counters[drink] = new_counter
        # 3 consecutive successes establish favorite (only if not yet set).
        if state.favorite_drink is None and state.repeat_counters[drink] >= 3:
            state.favorite_drink = drink

    # Update success_counter and generous_counter
    state.success_counter += 1
    if level == "generous":
        state.generous_counter += 1
    else:
        # generous_counter resets on leaving generous (any non-generous success).
        state.generous_counter = 0

    # Build response.
    new_level = mood_level(state.mood_score)
    body: dict = {
        "status": "ok",
        "drink": drink,
        "price": price,
    }
    if free_every_7th:
        body["free_every_7th"] = True
    elif generous_free:
        body["generous_free"] = True
    elif in_fav_window:
        body["favorite"] = True

    # Hint check.
    h = hint_for(state.success_counter)
    if h:
        body["hint"] = h

    body["balance"] = state.balance
    body["mood_level"] = new_level
    return body


def serve_secret(state: BarState, drink: str, effect: str) -> dict:
    """Apply a secret drink effect (no debit, no repeat counters, no favorite tracking)."""
    # Mood deltas first (special cases).
    if effect == "mood_max":
        state.mood_score = 98
    elif effect == "armageddon":
        # apply_secret_effect handles mood + bar_closed + reopens_at + balance.
        pass
    elif drink == "Мертвец":
        # First time: −32, floor 0.
        state.mood_score = clamp_mood(state.mood_score - 32)
    else:
        # Default: −2 (e.g. Зелье бармена).
        state.mood_score = clamp_mood(state.mood_score - 2)

    # Apply structural effect (sets balance for Армагеддон, doubles for Мертвец, etc.).
    apply_secret_effect(state, effect)

    state.history.append(HistoryEntry(drink=drink, price=0, method="mix"))
    state.success_counter += 1
    if mood_level(state.mood_score) == "generous":
        state.generous_counter += 1
    else:
        state.generous_counter = 0

    body: dict = {
        "status": "ok",
        "drink": drink,
        "price": 0,
        "secret": True,
        "effect": effect,
        "balance": state.balance,
        "mood_level": mood_level(state.mood_score),
    }
    h = hint_for(state.success_counter)
    if h:
        # Hint appears AFTER secret/effect fields, before balance? Actually the live API
        # places balance at the very end. Insert hint before balance.
        body = {
            "status": "ok",
            "drink": drink,
            "price": 0,
            "secret": True,
            "effect": effect,
            "hint": h,
            "balance": state.balance,
            "mood_level": mood_level(state.mood_score),
        }
    return body


def serve_air(state: BarState) -> dict:
    """`/mix []` → Воздух (no `secret:true`)."""
    state.mood_score = clamp_mood(state.mood_score + DELTA.get("Воздух", -2))
    state.history.append(HistoryEntry(drink="Воздух", price=0, method="mix"))
    state.success_counter += 1
    if mood_level(state.mood_score) == "generous":
        state.generous_counter += 1
    else:
        state.generous_counter = 0
    body = {
        "status": "ok",
        "drink": "Воздух",
        "price": 0,
        "balance": state.balance,
        "mood_level": mood_level(state.mood_score),
    }
    h = hint_for(state.success_counter)
    if h:
        body = {
            "status": "ok",
            "drink": "Воздух",
            "price": 0,
            "hint": h,
            "balance": state.balance,
            "mood_level": mood_level(state.mood_score),
        }
    return body
