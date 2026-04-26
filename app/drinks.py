"""Drink catalog and ingredient definitions for the Black Bartender clone."""
from __future__ import annotations

VALID_INGREDIENTS: tuple[str, ...] = (
    "водка",
    "ром",
    "текила",
    "виски",
    "джин",
    "кола",
    "сок",
    "тоник",
    "лёд",
    "молоко",
)

# Russian alphabetical ordering used by the live API when serialising ingredient lists.
_RU_ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
_RU_ORDER = {ch: i for i, ch in enumerate(_RU_ALPHABET)}


def ru_sort_key(s: str) -> tuple[int, ...]:
    return tuple(_RU_ORDER.get(ch, len(_RU_ALPHABET)) for ch in s)


def sort_ingredients_ru(ings: list[str]) -> list[str]:
    return sorted(ings, key=ru_sort_key)


# Drink → ingredient multiset (as a sorted-by-Russian-alphabet list).
DAY_DRINKS: dict[str, list[str]] = {
    "Куба Либре":      sort_ingredients_ru(["ром", "кола", "лёд"]),
    "Отвёртка":        sort_ingredients_ru(["водка", "сок"]),
    "Джин-тоник":      sort_ingredients_ru(["джин", "тоник", "лёд"]),
    "Виски-кола":      sort_ingredients_ru(["виски", "кола"]),
    "Текила-санрайз":  sort_ingredients_ru(["текила", "сок"]),
    "Русский":         sort_ingredients_ru(["водка", "лёд"]),
    "Белый русский":   sort_ingredients_ru(["водка", "лёд", "молоко"]),
    "Лонг-Айленд":     sort_ingredients_ru(["водка", "джин", "кола", "ром", "текила"]),
}

NIGHT_DRINKS: dict[str, list[str]] = {
    "Ночной русский":  sort_ingredients_ru(["водка", "лёд", "молоко"]),
    "Бессонница":      sort_ingredients_ru(["кола", "ром", "тоник"]),
    "Лунный свет":     sort_ingredients_ru(["джин", "сок", "тоник"]),
}

# Secret drinks: name → (frozenset of ingredient multiset, effect, response.secret_flag)
SECRET_DRINKS: dict[str, tuple[tuple[str, ...], str | None]] = {
    "Зелье бармена":  (tuple(sort_ingredients_ru(["джин", "сок", "тоник", "лёд"])),     "secret_unlocked"),
    "Ошибка бармена": (tuple(sort_ingredients_ru(["молоко", "текила", "лёд"])),         "mood_max"),
    "Мертвец":        (tuple(sort_ingredients_ru(["водка", "ром", "молоко"])),          "balance_doubled"),
    "Армагеддон":     (tuple(sort_ingredients_ru(["водка", "ром", "текила", "виски", "джин"])), "armageddon"),
}

CROWN_NAME = "Коронный"

# Day disambiguation: [водка, лёд, молоко] is Белый русский by day, Ночной русский by night.
WHITE_RUSSIAN_INGREDIENTS = tuple(sort_ingredients_ru(["водка", "лёд", "молоко"]))


def all_drinks() -> dict[str, list[str]]:
    return {**DAY_DRINKS, **NIGHT_DRINKS}


def drink_ingredients(name: str) -> list[str]:
    return all_drinks().get(name, [])


def find_by_ingredients(ings: list[str], time_of_day: str) -> str | None:
    """Match a sorted ingredient multiset to a drink name, given time_of_day ('day' or 'night').

    Returns the drink name or None.
    """
    key = tuple(sort_ingredients_ru(ings))
    # Exact match for day drinks (except white russian disambiguation).
    if key == WHITE_RUSSIAN_INGREDIENTS:
        return "Ночной русский" if time_of_day == "night" else "Белый русский"
    for name, recipe in DAY_DRINKS.items():
        if tuple(recipe) == key and name != "Белый русский":
            return name
    if time_of_day == "night":
        for name, recipe in NIGHT_DRINKS.items():
            if tuple(recipe) == key and name != "Ночной русский":
                return name
    return None


def find_secret(ings: list[str]) -> tuple[str, str] | None:
    """Match a sorted ingredient multiset to a secret drink. Returns (name, effect) or None."""
    key = tuple(sort_ingredients_ru(ings))
    for name, (recipe, effect) in SECRET_DRINKS.items():
        if recipe == key:
            return name, effect
    return None
