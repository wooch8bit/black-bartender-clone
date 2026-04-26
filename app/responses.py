"""Helpers to construct ordered JSON responses with stable key ordering matching the live API.

FastAPI / orjson preserves the dict insertion order so we just need to insert keys in the right
sequence.
"""
from __future__ import annotations

from app.mood import mood_level
from app.state import BarState


def with_balance_mood(payload: dict, state: BarState) -> dict:
    """Append balance + mood_level to a response payload, preserving order."""
    out = dict(payload)
    out["balance"] = state.balance
    out["mood_level"] = mood_level(state.mood_score)
    return out
