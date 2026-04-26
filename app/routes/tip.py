"""POST /tip — debit balance, raise mood by min(amount, 10)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_state
from app.models import TipRequest
from app.mood import clamp_mood, mood_level
from app.state import BarState

router = APIRouter()


@router.post("/tip")
async def tip(body: TipRequest, state: BarState = Depends(get_state)):
    amount = body.amount

    # Non-positive: invalid_amount (no mood/balance movement).
    if amount <= 0:
        return {
            "status": "error",
            "error": "invalid_amount",
            "balance": state.balance,
            "mood_level": mood_level(state.mood_score),
        }

    if amount > state.balance:
        return {
            "status": "error",
            "error": "insufficient_funds",
            "balance": state.balance,
            "mood_level": mood_level(state.mood_score),
        }

    state.balance -= amount
    state.mood_score = clamp_mood(state.mood_score + min(amount, 10))

    return {
        "status": "ok",
        "tip": amount,
        "balance": state.balance,
        "mood_level": mood_level(state.mood_score),
    }
