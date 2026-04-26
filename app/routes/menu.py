"""GET /menu — list available drinks for the requesting user.

Probed: night menu shows ONLY night drinks (Ночной русский / Бессонница / Лунный свет).
Day menu shows the 8 day drinks (and Crown if rank ≥ Мастер).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from app.auth import get_state
from app.crown import crown_recipe
from app.drinks import DAY_DRINKS, NIGHT_DRINKS
from app.mood import mood_level
from app.pricing import price_for
from app.ranks import rank_for
from app.state import BarState
from app.xtime import parse_xtime

router = APIRouter()


GENEROUS_NOTE = "Я сегодня добрый. Каждый третий — за счёт заведения."
FRIENDLY_NOTE = "Попробуй смешать что-нибудь сам — будет дешевле."


@router.get("/menu")
async def menu(state: BarState = Depends(get_state), x_time: str | None = Header(default=None, alias="X-Time")):
    level = mood_level(state.mood_score)

    if state.bar_closed:
        return {
            "status": "error",
            "error": "bar_closed",
            "reopens_at": state.reopens_at,
            "balance": state.balance,
            "mood_level": level,
        }

    period = parse_xtime(x_time)
    unique = len({h.drink for h in state.history})
    rank = rank_for(unique)

    drinks_src = DAY_DRINKS if period == "day" else NIGHT_DRINKS

    drinks = []
    for name, ings in drinks_src.items():
        drinks.append({
            "name": name,
            "price": price_for(name, level, rank=rank, method="order"),
            "ingredients": list(ings),
        })

    if rank == "Мастер":
        drinks.append({
            "name": "Коронный",
            "price": price_for("Коронный", level, rank=rank, method="order"),
            "ingredients": crown_recipe(state.history),
        })

    body: dict = {
        "status": "ok",
        "drinks": drinks,
        "balance": state.balance,
        "mood_level": level,
    }
    if level == "generous":
        body["note"] = GENEROUS_NOTE
    elif level == "friendly":
        body["note"] = FRIENDLY_NOTE
    return body
