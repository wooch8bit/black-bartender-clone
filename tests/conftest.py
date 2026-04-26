import pytest
from httpx import ASGITransport, AsyncClient

from app import storage
from app.main import create_app


@pytest.fixture
def app():
    storage._clear()
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
