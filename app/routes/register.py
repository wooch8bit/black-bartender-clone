"""POST /register — issue a new token + id."""
from __future__ import annotations

from fastapi import APIRouter

from app import storage

router = APIRouter()


@router.post("/register")
async def register():
    s = await storage.create()
    return {"status": "ok", "id": s.id, "token": s.token}
