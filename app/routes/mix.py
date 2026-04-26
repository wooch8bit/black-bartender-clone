"""POST /mix — combine raw ingredients."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from app.auth import get_state
from app.core import is_refused, serve_air, serve_regular_drink, serve_secret
from app.crown import crown_recipe
from app.drinks import (
    CROWN_NAME,
    VALID_INGREDIENTS,
    find_by_ingredients,
    find_secret,
    sort_ingredients_ru,
)
from app.mood import UNKNOWN_RECIPE_DELTA, clamp_mood, mood_level
from app.models import MixRequest
from app.ranks import rank_for
from app.state import BarState
from app.xtime import parse_xtime

router = APIRouter()


@router.post("/mix")
async def mix(
    body: MixRequest,
    state: BarState = Depends(get_state),
    x_time: str | None = Header(default=None, alias="X-Time"),
):
    if state.bar_closed:
        return {
            "status": "error",
            "error": "bar_closed",
            "reopens_at": state.reopens_at,
            "balance": state.balance,
            "mood_level": mood_level(state.mood_score),
        }

    ingredients = body.ingredients

    # Empty list → Воздух (special, no `secret:true`).
    if len(ingredients) == 0:
        return serve_air(state)

    # Validation: every ingredient must be in the 10-list.
    for ing in ingredients:
        if ing not in VALID_INGREDIENTS:
            return {
                "status": "error",
                "error": "invalid_ingredient",
                "balance": state.balance,
                "mood_level": mood_level(state.mood_score),
            }

    period = parse_xtime(x_time)

    # Secret drinks first.
    secret_match = find_secret(ingredients)
    if secret_match:
        name, effect = secret_match
        return serve_secret(state, name, effect)

    # Crown match (only at Мастер).
    if rank_for(len({h.drink for h in state.history})) == "Мастер":
        if tuple(sort_ingredients_ru(ingredients)) == tuple(crown_recipe(state.history)):
            level = mood_level(state.mood_score)
            if is_refused(CROWN_NAME, level):
                return {
                    "status": "error",
                    "error": "refused",
                    "drink": CROWN_NAME,
                    "balance": state.balance,
                    "mood_level": level,
                }
            return serve_regular_drink(state, CROWN_NAME, method="mix", is_crown=True)

    # Day/night recipe match.
    name = find_by_ingredients(ingredients, period)
    if name:
        level = mood_level(state.mood_score)
        if is_refused(name, level):
            return {
                "status": "error",
                "error": "refused",
                "drink": name,
                "balance": state.balance,
                "mood_level": level,
            }
        return serve_regular_drink(state, name, method="mix")

    # Unknown recipe.
    state.mood_score = clamp_mood(state.mood_score + UNKNOWN_RECIPE_DELTA)
    return {
        "status": "error",
        "error": "unknown_recipe",
        "balance": state.balance,
        "mood_level": mood_level(state.mood_score),
    }
