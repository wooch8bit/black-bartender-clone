"""Smoke tests for the local clone."""
import pytest

pytestmark = pytest.mark.asyncio


async def hdr(token, x="14:30"):
    return {"Authorization": f"Bearer {token}", "X-Time": x}


async def register(client):
    r = await client.post("/register")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["id"].startswith("BAR-")
    assert len(j["token"]) == 32
    return j["token"]


async def test_register_balance_profile_menu_reset(client):
    token = await register(client)
    h = await hdr(token)

    # /balance fresh
    r = await client.get("/balance", headers=h)
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "balance": 100, "mood_level": "normal"}

    # /profile fresh
    r = await client.get("/profile", headers=h)
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["rank"] == "Новичок"
    assert j["total_orders"] == 0
    assert j["unique_drinks"] == 0
    assert j["favorite_drink"] is None
    assert j["bar_closed"] is False

    # /menu day
    r = await client.get("/menu", headers=h)
    j = r.json()
    assert j["status"] == "ok"
    assert {d["name"] for d in j["drinks"]} == {
        "Куба Либре", "Отвёртка", "Джин-тоник", "Виски-кола",
        "Текила-санрайз", "Русский", "Белый русский", "Лонг-Айленд",
    }

    # /menu night → only night drinks
    r = await client.get("/menu", headers=await hdr(token, "02:30"))
    j = r.json()
    assert {d["name"] for d in j["drinks"]} == {"Ночной русский", "Бессонница", "Лунный свет"}

    # /reset
    r = await client.post("/reset", headers=h)
    assert r.json() == {"status": "ok"}


async def test_auth_matrix(client):
    token = await register(client)

    # Wrong tokens
    for hh in [
        None,
        "Bearer ",
        "Bearer ".strip(),  # "Bearer"
        "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "bearer " + token,
        "BEARER " + token,
        "Token " + token,
        "Basic " + token,
    ]:
        headers = {"X-Time": "14:30"}
        if hh is not None:
            headers["Authorization"] = hh
        r = await client.get("/balance", headers=headers)
        assert r.status_code == 401, (hh, r.json())
        assert r.json() == {"detail": {"status": "error", "error": "unauthorized"}}

    # Accepted forms: Bearer <t>, Bearer  <t> (double space), <t>
    for hh in [f"Bearer {token}", f"Bearer  {token}", token]:
        r = await client.get("/balance", headers={"Authorization": hh})
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


async def test_order_basic(client):
    token = await register(client)
    h = await hdr(token)

    r = await client.post("/order", headers=h, json={"name": "Куба Либре"})
    assert r.json() == {
        "status": "ok",
        "drink": "Куба Либре",
        "price": 15,
        "balance": 85,
        "mood_level": "normal",
    }

    r = await client.post("/order", headers=h, json={"name": "Русский"})
    j = r.json()
    assert j["status"] == "ok"
    assert j["drink"] == "Русский"
    # Russky -5 mood: 50 - 2 (KL) - 5 = 43 → still normal
    assert j["mood_level"] == "normal"

    r = await client.post("/order", headers=h, json={"name": "Unknown"})
    assert r.json()["error"] == "unknown_drink"


async def test_unknown_recipe_drops_mood(client):
    token = await register(client)
    h = await hdr(token)

    # 50 → 45 (-5)
    r = await client.post("/mix", headers=h, json={"ingredients": ["сок", "ром"]})
    assert r.json()["error"] == "unknown_recipe"
    assert r.json()["mood_level"] == "normal"  # 45 still normal


async def test_invalid_ingredient(client):
    token = await register(client)
    h = await hdr(token)
    r = await client.post("/mix", headers=h, json={"ingredients": ["vodka"]})
    assert r.json() == {
        "status": "error",
        "error": "invalid_ingredient",
        "balance": 100,
        "mood_level": "normal",
    }


async def test_air(client):
    token = await register(client)
    h = await hdr(token)
    r = await client.post("/mix", headers=h, json={"ingredients": []})
    j = r.json()
    assert j["drink"] == "Воздух"
    assert j["price"] == 0
    assert "secret" not in j


async def test_secret_unlock(client):
    token = await register(client)
    h = await hdr(token)

    r = await client.get("/secret", headers=h)
    assert r.json() == {"status": "error", "error": "not_found"}

    r = await client.post("/mix", headers=h, json={"ingredients": ["джин", "сок", "тоник", "лёд"]})
    j = r.json()
    assert j["drink"] == "Зелье бармена"
    assert j["secret"] is True
    assert j["effect"] == "secret_unlocked"

    r = await client.get("/secret", headers=h)
    j = r.json()
    assert j["status"] == "ok"
    assert isinstance(j["mood"], int)


async def test_armageddon(client):
    token = await register(client)
    h = await hdr(token)
    r = await client.post("/mix", headers=h, json={"ingredients": ["водка", "ром", "текила", "виски", "джин"]})
    j = r.json()
    assert j["drink"] == "Армагеддон"
    assert j["effect"] == "armageddon"
    assert j["balance"] == 0
    assert j["mood_level"] == "hostile"

    # /menu now bar_closed
    r = await client.get("/menu", headers=h)
    j = r.json()
    assert j["status"] == "error"
    assert j["error"] == "bar_closed"
    assert j["reopens_at"]


async def test_refused_in_hostile(client):
    token = await register(client)
    h = await hdr(token)
    # Drop to hostile: Zelie + Mertvets
    await client.post("/mix", headers=h, json={"ingredients": ["джин", "сок", "тоник", "лёд"]})
    await client.post("/mix", headers=h, json={"ingredients": ["водка", "ром", "молоко"]})
    r = await client.post("/order", headers=h, json={"name": "Белый русский"})
    j = r.json()
    assert j["status"] == "error"
    assert j["error"] == "refused"
    assert j["drink"] == "Белый русский"

    r = await client.post("/order", headers=h, json={"name": "Куба Либре"})
    assert r.json()["status"] == "ok"


async def test_repeat_cycle(client):
    token = await register(client)
    h = await hdr(token)
    # Tip up balance to afford 7+ KL orders.
    await client.post("/tip", headers=h, json={"amount": -1})  # invalid_amount, no movement
    # Order KL up to the prompt
    seq = []
    for i in range(8):
        r = await client.post("/order", headers=h, json={"name": "Куба Либре"})
        seq.append(r.json())
    # 5th = prompt
    assert seq[4]["status"] == "prompt"
    assert seq[4]["prompt"] == "repeat_check"
    # 4th = favorite
    assert seq[3].get("favorite") is True
    assert seq[3]["price"] == 12  # base 15 → 0.8 = 12
    # 8th call (after the prompt at index 4 didn't increment) is the 7th paid → free_every_7th
    # Actually free fires on 7 paid in the cycle. Find first free in seq.
    free = [s for s in seq if s.get("free_every_7th")]
    assert free, seq


async def test_history_keys(client):
    token = await register(client)
    h = await hdr(token)
    await client.post("/order", headers=h, json={"name": "Куба Либре"})
    await client.post("/mix", headers=h, json={"ingredients": []})
    r = await client.get("/history", headers=h)
    j = r.json()
    assert j["status"] == "ok"
    assert "orders" in j
    assert j["orders"][0]["drink"] == "Куба Либре"
    assert j["orders"][1]["drink"] == "Воздух"
    assert "balance" in j and "mood_level" in j


async def test_xtime_parsing(client):
    token = await register(client)
    cases = {
        "24:00": "Ночной русский",  # night
        "99:99": "Ночной русский",  # 99%24 = 3 night
        "ab:cd": "Куба Либре",     # day
        "06:60": "Куба Либре",     # day
        "-1:00": "Куба Либре",     # day (-1%24=23)
        "00:00": "Ночной русский",  # night
        "05:59": "Ночной русский",  # night
        "06:00": "Куба Либре",     # day
        "100:00": "Ночной русский",  # 100%24=4 night
    }
    for x, first in cases.items():
        r = await client.get("/menu", headers={"Authorization": f"Bearer {token}", "X-Time": x})
        names = [d["name"] for d in r.json()["drinks"]]
        assert names[0] == first, (x, names)
