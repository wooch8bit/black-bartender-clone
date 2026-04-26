"""Mood scoring and Δmood deltas per drink/event."""
from __future__ import annotations


def mood_level(score: int) -> str:
    if score >= 80:
        return "generous"
    if score >= 60:
        return "friendly"
    if score >= 40:
        return "normal"
    if score >= 20:
        return "grumpy"
    return "hostile"


def clamp_mood(score: int) -> int:
    return max(0, min(98, score))


# Δmood per drink success (in `normal`; same for other moods unless overridden).
DELTA: dict[str, int] = {
    "Куба Либре": -2,
    "Отвёртка": -2,
    "Джин-тоник": -2,
    "Виски-кола": -2,
    "Текила-санрайз": -2,
    "Русский": -5,           # special — boring
    "Белый русский": -2,
    "Лонг-Айленд": +3,        # special — respect
    "Ночной русский": -2,
    "Бессонница": -2,
    "Лунный свет": -2,
    "Коронный": -2,
    "Зелье бармена": -2,
    "Воздух": -2,
    # Ошибка бармена → SETS to 98
    # Мертвец → −32 first, floor 0
    # Армагеддон → SETS to 0
}


# In `generous` mood every drink is treated as -2 (per spec note in prompt §9.2).
def delta_for(drink: str, current_level: str) -> int:
    if current_level == "generous":
        return -2
    return DELTA.get(drink, -2)


UNKNOWN_RECIPE_DELTA = -5
