from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_organization_id, get_current_user_id, get_db
from app.main import app


class DummySession:
    async def execute(self, *args, **kwargs):
        return None

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def flush(self):
        return None

    async def refresh(self, *_args, **_kwargs):
        return None

    async def delete(self, *_args, **_kwargs):
        return None

    def add(self, *_args, **_kwargs):
        return None


@pytest.fixture
def sample_user():
    return SimpleNamespace(
        id=1,
        email="jane@example.com",
        full_name="Jane Doe",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        hashed_password="hashed-password",
    )


@pytest.fixture
def client():
    async def override_get_db():
        yield DummySession()

    async def override_get_current_user_id():
        return 1

    async def override_get_current_organization_id():
        return 1

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[get_current_organization_id] = override_get_current_organization_id

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
