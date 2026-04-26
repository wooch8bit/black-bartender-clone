"""POST /reset — wipe state, keep token."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_state
from app.state import BarState

router = APIRouter()


@router.post("/reset")
async def reset(state: BarState = Depends(get_state)):
    state.reset()
    return {"status": "ok"}
