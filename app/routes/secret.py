"""GET /secret — current mood score, only after Зелье бармена unlock."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_state
from app.state import BarState

router = APIRouter()


@router.get("/secret")
async def secret(state: BarState = Depends(get_state)):
    if not state.secret_unlocked:
        return {"status": "error", "error": "not_found"}
    return {"status": "ok", "mood": state.mood_score}
