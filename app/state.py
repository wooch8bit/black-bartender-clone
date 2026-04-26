"""Per-token state."""
from __future__ import annotations

from dataclasses import dataclass, field
import secrets


_id_counter = 0


def _new_id() -> str:
    global _id_counter
    _id_counter += 1
    # BAR-XXXXX (5 digits, may wrap)
    return f"BAR-{_id_counter % 100000:05d}"


def _new_token() -> str:
    return secrets.token_hex(16)


@dataclass
class HistoryEntry:
    drink: str
    price: int
    method: str  # "order" or "mix"


@dataclass
class BarState:
    id: str = field(default_factory=_new_id)
    token: str = field(default_factory=_new_token)
    balance: int = 100
    mood_score: int = 50
    history: list[HistoryEntry] = field(default_factory=list)
    secret_unlocked: bool = False
    bar_closed: bool = False
    reopens_at: str | None = None
    favorite_drink: str | None = None
    repeat_counters: dict[str, int] = field(default_factory=dict)
    last_drink: str | None = None  # for "consecutive" repeat tracking
    consecutive_count: int = 0
    pending_repeat_check: str | None = None
    free_used: bool = False  # whether free_every_7th has fired in current cycle
    seven_counter: int = 0  # successful repeats since last free
    generous_counter: int = 0  # successful order/mix in generous since last reset
    success_counter: int = 0  # global successful order/mix
    hints_seen: set[int] = field(default_factory=set)

    def reset(self) -> None:
        self.balance = 100
        self.mood_score = 50
        self.history = []
        self.secret_unlocked = False
        self.bar_closed = False
        self.reopens_at = None
        self.favorite_drink = None
        self.repeat_counters = {}
        self.last_drink = None
        self.consecutive_count = 0
        self.pending_repeat_check = None
        self.free_used = False
        self.seven_counter = 0
        self.generous_counter = 0
        self.success_counter = 0
        self.hints_seen = set()
