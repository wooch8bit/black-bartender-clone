"""In-memory token store."""
from __future__ import annotations

import asyncio

from app.state import BarState

_states: dict[str, BarState] = {}
_lock = asyncio.Lock()


async def create() -> BarState:
    async with _lock:
        s = BarState()
        # Avoid an astronomically unlikely collision.
        while s.token in _states:
            s = BarState()
        _states[s.token] = s
        return s


def get(token: str) -> BarState | None:
    return _states.get(token)


def lock() -> asyncio.Lock:
    return _lock


def _clear() -> None:
    """Test helper: wipe the store."""
    _states.clear()
