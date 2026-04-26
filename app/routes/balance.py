"""GET /balance — current balance and mood_level."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_state
from app.mood import mood_level
from app.state import BarState

router = APIRouter()


FRIENDLY_BALANCE_NOTE = "Чаевые всегда поднимают мне настроение."


@router.get("/balance")
async def balance(state: BarState = Depends(get_state)):
    level = mood_level(state.mood_score)
    body: dict = {
        "status": "ok",
        "balance": state.balance,
        "mood_level": level,
    }
    if level == "friendly":
        body["note"] = FRIENDLY_BALANCE_NOTE
    return body
