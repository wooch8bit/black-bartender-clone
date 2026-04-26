"""X-Time header parser."""
from __future__ import annotations

from typing import Literal


def parse_xtime(header: str | None) -> Literal["day", "night"]:
    """Parse the X-Time header.

    - Format: "HH:MM" (minutes ignored entirely).
    - HH parsed as int(HH) % 24.
    - night = result in [0, 5]; day = [6, 23].
    - Empty / missing / unparseable → "day".
    """
    if not header:
        return "day"
    try:
        h = int(header.strip().split(":", 1)[0]) % 24
    except Exception:
        return "day"
    return "night" if h < 6 else "day"
