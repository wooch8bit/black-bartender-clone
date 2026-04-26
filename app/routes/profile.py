"""GET /profile — id, rank, totals, favorite, bar_closed flag."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_state
from app.ranks import rank_for
from app.state import BarState

router = APIRouter()


@router.get("/profile")
async def profile(state: BarState = Depends(get_state)):
    unique = len({h.drink for h in state.history})
    return {
        "status": "ok",
        "id": state.id,
        "rank": rank_for(unique),
        "total_orders": len(state.history),
        "unique_drinks": unique,
        "favorite_drink": state.favorite_drink,
        "bar_closed": state.bar_closed,
    }
