"""Authorization dependency: 3 accepted forms, detail-wrapped 401."""
from __future__ import annotations

from fastapi import Header, HTTPException

from app import storage
from app.state import BarState


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail={"status": "error", "error": "unauthorized"})


def extract_token(authorization: str | None) -> str | None:
    """Return the token if the header is one of the 3 accepted forms, else None.

    Accepted forms:
      - "Bearer <token>"
      - "Bearer  <token>" (any extra whitespace after Bearer is fine)
      - "<token>" (no Bearer prefix at all)

    Anything else (lowercase 'bearer', 'BEARER', 'Token', 'Basic', empty value, etc.) is rejected.
    """
    if not authorization:
        return None
    raw = authorization
    # Tolerant trim: live API accepts surrounding whitespace.
    if raw.startswith("Bearer"):
        # Must be followed by whitespace AND then a non-empty token.
        rest = raw[len("Bearer"):]
        if not rest:
            return None
        if rest[0] not in (" ", "\t"):
            # "Bearer<token>" with no whitespace is rejected.
            return None
        token = rest.strip()
        return token or None
    # Reject any non-Bearer scheme like "Basic ...", "Token ...", "JWT ..."
    head = raw.split(maxsplit=1)
    if head and len(head[0]) > 0 and " " in raw:
        # If there's a leading word ending in space, it's a scheme — reject (since not "Bearer").
        return None
    return raw.strip() or None


async def get_state(authorization: str | None = Header(None)) -> BarState:
    token = extract_token(authorization)
    if not token:
        raise _unauthorized()
    state = storage.get(token)
    if not state:
        raise _unauthorized()
    return state
