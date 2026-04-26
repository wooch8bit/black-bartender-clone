"""Rank thresholds.

Probed against the live API by walking unique_drinks 0 → 11:
  0–2  → Новичок
  3–4  → Гость
  5–7  → Постоянный
  8–10 → Знаток
  11+  → Мастер
"""
from __future__ import annotations

# (min_unique, rank_name) thresholds. Pick the highest match.
THRESHOLDS = [
    (0, "Новичок"),
    (3, "Гость"),
    (5, "Постоянный"),
    (8, "Знаток"),
    (11, "Мастер"),
]


def rank_for(unique_drinks: int) -> str:
    out = "Новичок"
    for thr, name in THRESHOLDS:
        if unique_drinks >= thr:
            out = name
    return out
