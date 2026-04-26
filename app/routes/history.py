"""GET /history — list of successful orders/mixes."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_state
from app.mood import mood_level
from app.state import BarState

router = APIRouter()


@router.get("/history")
async def history(state: BarState = Depends(get_state)):
    return {
        "status": "ok",
        "orders": [
            {"drink": h.drink, "price": h.price, "method": h.method}
            for h in state.history
        ],
        "balance": state.balance,
        "mood_level": mood_level(state.mood_score),
    }
