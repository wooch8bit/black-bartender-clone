"""Differential tests: each scenario runs against both the live API and the local clone,
asserting that the HTTP status and JSON body match exactly.

Skipped automatically when the live API is unreachable (or when LIVE_DIFF=0 is set).
"""
from __future__ import annotations

import os
import time
import asyncio

import pytest
import httpx
from httpx import ASGITransport, AsyncClient

from app import storage
from app.main import create_app

LIVE = "https://bar.antihype.lol"
RUN = os.environ.get("LIVE_DIFF") not in ("0", "false", "")


def _live_reachable() -> bool:
    if not RUN:
        return False
    try:
        with httpx.Client(timeout=5) as c:
            r = c.get(f"{LIVE}/balance", headers={"Authorization": "Bearer x"})
            return r.status_code == 401
    except Exception:
        return False


pytestmark = [pytest.mark.skipif(not _live_reachable(), reason="live API not reachable / LIVE_DIFF=0")]


async def _call(c, method, path, retries=4, **kw):
    last = None
    for _ in range(retries):
        r = await c.request(method, path, **kw)
        if r.status_code == 429:
            await asyncio.sleep(r.json().get("retry_after", 5) + 0.5)
            continue
        last = r
        return r
    return last


def _drop_keys(obj, keys=("token", "id", "reopens_at")):
    """Strip volatile fields so live and clone bodies can be compared structurally."""
    if isinstance(obj, dict):
        return {k: _drop_keys(v, keys) for k, v in obj.items() if k not in keys}
    if isinstance(obj, list):
        return [_drop_keys(x, keys) for x in obj]
    return obj


@pytest.fixture
async def live():
    async with httpx.AsyncClient(base_url=LIVE, timeout=20) as c:
        yield c


@pytest.fixture
async def clone():
    storage._clear()
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _new_pair(live, clone):
    rl = await _call(live, "POST", "/register")
    rc = await _call(clone, "POST", "/register")
    assert rl.status_code == rc.status_code == 200
    tl = rl.json()["token"]
    tc = rc.json()["token"]
    return tl, tc


def _h(t, x="14:30"):
    return {"Authorization": f"Bearer {t}", "X-Time": x}


@pytest.mark.asyncio
async def test_S1_register_balance_profile_menu_reset(live, clone):
    tl, tc = await _new_pair(live, clone)

    rl = await _call(live, "GET", "/balance", headers=_h(tl))
    rc = await _call(clone, "GET", "/balance", headers=_h(tc))
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())

    rl = await _call(live, "GET", "/profile", headers=_h(tl))
    rc = await _call(clone, "GET", "/profile", headers=_h(tc))
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())

    rl = await _call(live, "GET", "/menu", headers=_h(tl))
    rc = await _call(clone, "GET", "/menu", headers=_h(tc))
    assert _drop_keys(rl.json()) == _drop_keys(rc.json()), (rl.json(), rc.json())

    rl = await _call(live, "GET", "/menu", headers=_h(tl, "02:30"))
    rc = await _call(clone, "GET", "/menu", headers=_h(tc, "02:30"))
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())

    rl = await _call(live, "POST", "/reset", headers=_h(tl))
    rc = await _call(clone, "POST", "/reset", headers=_h(tc))
    assert rl.json() == rc.json()


@pytest.mark.asyncio
async def test_S2_basic_order(live, clone):
    tl, tc = await _new_pair(live, clone)
    for body in [{"name": "Куба Либре"}, {"name": "Русский"}, {"name": "Куба Либре"}]:
        rl = await _call(live, "POST", "/order", headers=_h(tl), json=body)
        rc = await _call(clone, "POST", "/order", headers=_h(tc), json=body)
        assert _drop_keys(rl.json()) == _drop_keys(rc.json()), (body, rl.json(), rc.json())


@pytest.mark.asyncio
async def test_S3_auth(live, clone):
    """Wrong tokens / missing auth → identical 401 detail wrap."""
    # Note: skip "Bearer " (trailing space) — httpx rejects whitespace headers.
    for h in [{}, {"Authorization": "Bearer"},
              {"Authorization": "bearer x"}, {"Authorization": "Token x"}]:
        rl = await _call(live, "GET", "/balance", headers={**h, "X-Time": "14:30"})
        rc = await _call(clone, "GET", "/balance", headers={**h, "X-Time": "14:30"})
        assert (rl.status_code, rl.json()) == (rc.status_code, rc.json()), (h, rl.json(), rc.json())


@pytest.mark.asyncio
async def test_S5_secret_unlock(live, clone):
    tl, tc = await _new_pair(live, clone)
    body = {"ingredients": ["джин", "сок", "тоник", "лёд"]}
    rl = await _call(live, "POST", "/mix", headers=_h(tl), json=body)
    rc = await _call(clone, "POST", "/mix", headers=_h(tc), json=body)
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())

    rl = await _call(live, "GET", "/secret", headers=_h(tl))
    rc = await _call(clone, "GET", "/secret", headers=_h(tc))
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())


@pytest.mark.asyncio
async def test_S7_hostile(live, clone):
    tl, tc = await _new_pair(live, clone)
    for ing in [["джин", "сок", "тоник", "лёд"], ["водка", "ром", "молоко"]]:
        await _call(live, "POST", "/mix", headers=_h(tl), json={"ingredients": ing})
        await _call(clone, "POST", "/mix", headers=_h(tc), json={"ingredients": ing})

    rl = await _call(live, "POST", "/order", headers=_h(tl), json={"name": "Белый русский"})
    rc = await _call(clone, "POST", "/order", headers=_h(tc), json={"name": "Белый русский"})
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())

    rl = await _call(live, "POST", "/order", headers=_h(tl), json={"name": "Куба Либре"})
    rc = await _call(clone, "POST", "/order", headers=_h(tc), json={"name": "Куба Либре"})
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())


@pytest.mark.asyncio
async def test_S9_armageddon(live, clone):
    tl, tc = await _new_pair(live, clone)
    body = {"ingredients": ["водка", "ром", "текила", "виски", "джин"]}
    rl = await _call(live, "POST", "/mix", headers=_h(tl), json=body)
    rc = await _call(clone, "POST", "/mix", headers=_h(tc), json=body)
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())

    rl = await _call(live, "GET", "/menu", headers=_h(tl))
    rc = await _call(clone, "GET", "/menu", headers=_h(tc))
    # Both should be bar_closed; reopens_at differs (timing) — drop it.
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())

    rl = await _call(live, "GET", "/profile", headers=_h(tl))
    rc = await _call(clone, "GET", "/profile", headers=_h(tc))
    assert _drop_keys(rl.json()) == _drop_keys(rc.json())


@pytest.mark.asyncio
async def test_S11_hints_at_8_9_10(live, clone):
    tl, tc = await _new_pair(live, clone)
    # 7 successful orders, then 8th, 9th, 10th — track hints
    sequence = [
        ("order", {"name": "Куба Либре"}),
        ("order", {"name": "Куба Либре"}),
        ("order", {"name": "Куба Либре"}),
        ("order", {"name": "Куба Либре"}),  # 4 KL → favorite (skip 5th prompt)
        ("order", {"name": "Куба Либре"}),  # 5: prompt
        ("order", {"name": "Куба Либре"}),  # 6
        ("order", {"name": "Куба Либре"}),  # 7
        ("order", {"name": "Куба Либре"}),  # 8 — should free
        ("order", {"name": "Отвёртка"}),    # 9 — different drink
        ("order", {"name": "Отвёртка"}),    # 10 — should fire hint
    ]
    for kind, body in sequence:
        rl = await _call(live, "POST", f"/{kind}", headers=_h(tl), json=body)
        rc = await _call(clone, "POST", f"/{kind}", headers=_h(tc), json=body)
        assert _drop_keys(rl.json()) == _drop_keys(rc.json()), (kind, body, rl.json(), rc.json())


@pytest.mark.asyncio
async def test_S12_method_not_allowed(live, clone):
    rl = await _call(live, "GET", "/order")
    rc = await _call(clone, "GET", "/order")
    assert (rl.status_code, rl.json()) == (rc.status_code, rc.json())

    rl = await _call(live, "POST", "/balance")
    rc = await _call(clone, "POST", "/balance")
    assert (rl.status_code, rl.json()) == (rc.status_code, rc.json())

    rl = await _call(live, "GET", "/health")
    rc = await _call(clone, "GET", "/health")
    assert rl.status_code == rc.status_code == 404


@pytest.mark.asyncio
async def test_xtime_matrix(live, clone):
    tl, tc = await _new_pair(live, clone)
    for x in ["24:00", "99:99", "ab:cd", "00:00", "06:00", "100:00"]:
        rl = await _call(live, "GET", "/menu", headers=_h(tl, x))
        rc = await _call(clone, "GET", "/menu", headers=_h(tc, x))
        ln = [d["name"] for d in rl.json()["drinks"]]
        cn = [d["name"] for d in rc.json()["drinks"]]
        assert set(ln) == set(cn), (x, ln, cn)
