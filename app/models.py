"""Pydantic models for request bodies."""
from __future__ import annotations

from pydantic import BaseModel


class OrderRequest(BaseModel):
    name: str


class MixRequest(BaseModel):
    ingredients: list[str]


class TipRequest(BaseModel):
    amount: int
