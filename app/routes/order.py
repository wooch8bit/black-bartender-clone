"""POST /order — pay for a named drink."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from app.auth import get_state
from app.core import is_refused, serve_regular_drink
from app.crown import crown_recipe
from app.drinks import CROWN_NAME, DAY_DRINKS, NIGHT_DRINKS
from app.mood import mood_level
from app.models import OrderRequest
from app.ranks import rank_for
from app.state import BarState
from app.xtime import parse_xtime

router = APIRouter()


@router.post("/order")
async def order(
    body: OrderRequest,
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

    name = body.name
    period = parse_xtime(x_time)
    level = mood_level(state.mood_score)

    # Drink resolution
    if name in DAY_DRINKS:
        pass
    elif name in NIGHT_DRINKS:
        if period != "night":
            return {
                "status": "error",
                "error": "unknown_drink",
                "balance": state.balance,
                "mood_level": level,
            }
    elif name == CROWN_NAME:
        # Only at Мастер.
        if rank_for(len({h.drink for h in state.history})) != "Мастер":
            return {
                "status": "error",
                "error": "unknown_drink",
                "balance": state.balance,
                "mood_level": level,
            }
    else:
        return {
            "status": "error",
            "error": "unknown_drink",
            "balance": state.balance,
            "mood_level": level,
        }

    if is_refused(name, level):
        return {
            "status": "error",
            "error": "refused",
            "drink": name,
            "balance": state.balance,
            "mood_level": level,
        }

    return serve_regular_drink(state, name, method="order", is_crown=(name == CROWN_NAME))
