"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI

from app.routes import balance, history, menu, mix, order, profile, register, reset, secret, tip


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    app.include_router(register.router)
    app.include_router(reset.router)
    app.include_router(menu.router)
    app.include_router(order.router)
    app.include_router(mix.router)
    app.include_router(history.router)
    app.include_router(profile.router)
    app.include_router(balance.router)
    app.include_router(tip.router)
    app.include_router(secret.router)

    return app


app = create_app()
