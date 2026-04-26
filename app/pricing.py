"""Drink pricing.

Probed (rank=Новичок) base prices (mood=normal):

  Куба Либре      15
  Отвёртка        12
  Джин-тоник      14
  Виски-кола      13
  Текила-санрайз  14
  Русский         10
  Белый русский   16
  Лонг-Айленд     25
  Ночной русский   8
  Бессонница      10
  Лунный свет     12

Mood multipliers (verified by probing the live /menu at every mood):

  hostile:  ceil(normal * 1.5)
  grumpy:   ceil(normal * 1.2)
  normal:   normal
  friendly: floor(normal * 0.9)
  generous: floor(normal * 0.75)

Rank effect: spec §11 mentions at least two tiers (Новичок/Гость vs Постоянный/Знаток/Мастер);
exact thresholds are TBD. Until probed further, we treat all ranks as the Новичок tier.
This maximises agreement with the most common starting state observed in differential tests.

Crown (Коронный) Master price defaults to 4 in `normal` (range 3–5 per spec §7.4); subject to
probing once we can reach Мастер reliably.
"""
from __future__ import annotations

import math


BASE_NORMAL_PRICE: dict[str, int] = {
    "Куба Либре":      15,
    "Отвёртка":        12,
    "Джин-тоник":      14,
    "Виски-кола":      13,
    "Текила-санрайз":  14,
    "Русский":         10,
    "Белый русский":   16,
    "Лонг-Айленд":     25,
    "Ночной русский":   8,
    "Бессонница":      10,
    "Лунный свет":     12,
    "Коронный":         4,
}


def _mood_adjust(price: int, level: str) -> int:
    if level == "hostile":
        return math.ceil(price * 1.5)
    if level == "grumpy":
        return math.ceil(price * 1.2)
    if level == "normal":
        return price
    if level == "friendly":
        return math.floor(price * 0.9)
    if level == "generous":
        return math.floor(price * 0.75)
    return price


def price_for(drink: str, mood_level_str: str, *, rank: str = "Новичок", method: str = "order") -> int:
    """Return the price the live API would charge."""
    base = BASE_NORMAL_PRICE.get(drink, 0)
    if base == 0:
        return 0
    return _mood_adjust(base, mood_level_str)


def favorite_price(drink: str) -> int:
    """Discounted price applied while a drink is the active favorite (counters 4-7).

    Probed: KL favorite price = 12 across normal and grumpy moods → it is mood-independent
    and equals floor(base_normal * 0.8).
    """
    base = BASE_NORMAL_PRICE.get(drink, 0)
    return math.floor(base * 0.8)
