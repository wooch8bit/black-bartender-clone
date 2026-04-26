"""Easter-egg hints fired on the global success_counter.

From spec §10:
  #8  → "Говорят, молоко и текила — интересное сочетание..."   (hints at Ошибка бармена)
  #9  → "Все пять крепких в одном стакане? Кто-то пробовал..."  (hints at Армагеддон)
  #10 → "Джин, сок, тоник, лёд — бармен одобряет."              (hints at Зелье бармена)
"""
from __future__ import annotations

HINTS: dict[int, str] = {
    8:  "Говорят, молоко и текила — интересное сочетание...",
    9:  "Все пять крепких в одном стакане? Кто-то пробовал...",
    10: "Джин, сок, тоник, лёд — бармен одобряет.",
}


def hint_for(success_counter: int) -> str | None:
    return HINTS.get(success_counter)
