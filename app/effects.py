"""Apply secret-drink effects."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.state import BarState

# Server timezone is UTC+5 (Yekaterinburg / contest venue).
SERVER_TZ = timezone(timedelta(hours=5))

# After Армагеддон the bar reopens at server_now + reopen_delay.
# Probed: a Армагеддон at server-time 13:36 reopened at 13:51 → +0:15. Defaulting to 15 min.
REOPEN_DELAY = timedelta(minutes=15)


def apply_secret_effect(state: BarState, effect: str) -> None:
    if effect == "secret_unlocked":
        state.secret_unlocked = True
    elif effect == "mood_max":
        state.mood_score = 98
    elif effect == "balance_doubled":
        state.balance = state.balance * 2
    elif effect == "armageddon":
        state.mood_score = 0
        state.bar_closed = True
        state.balance = 0
        now = datetime.now(SERVER_TZ)
        reopen = (now + REOPEN_DELAY).time()
        state.reopens_at = f"{reopen.hour:02d}:{reopen.minute:02d}"
