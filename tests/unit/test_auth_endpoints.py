from app.core.security import create_access_token, create_refresh_token
from app.schemas.token import Token
from app.services.auth import AuthService
from app.services.user import UserService


def test_register_success(client, sample_user, monkeypatch):
    async def fake_register(self, email, full_name, password):
        return sample_user

    monkeypatch.setattr(AuthService, "register", fake_register)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": sample_user.email,
            "full_name": sample_user.full_name,
            "password": "Password123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == sample_user.email


def test_login_success(client, sample_user, monkeypatch):
    async def fake_login(self, email, password):
        return sample_user

    async def fake_generate_tokens(self, user):
        access_token, _, _ = create_access_token(subject=user.id, extra={"current_organization_id": 1})
        refresh_token, _, _ = create_refresh_token(subject=user.id, extra={"current_organization_id": 1})
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    monkeypatch.setattr(AuthService, "login", fake_login)
    monkeypatch.setattr(AuthService, "generate_tokens", fake_generate_tokens)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": sample_user.email, "password": "Password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert "refresh_token" in body


def test_refresh_success(client, monkeypatch):
    async def fake_refresh(self, refresh_token):
        access_token, _, _ = create_access_token(subject=1, extra={"current_organization_id": 1})
        refresh_token_value, _, _ = create_refresh_token(subject=1, extra={"current_organization_id": 1})
        return Token(
            access_token=access_token,
            refresh_token=refresh_token_value,
        )

    monkeypatch.setattr(AuthService, "refresh_access_token", fake_refresh)

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "refresh-token"})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_get_auth_me_success(client, sample_user, monkeypatch):
    async def fake_get_by_id(self, user_id):
        return sample_user

    monkeypatch.setattr(UserService, "get_by_id", fake_get_by_id)

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["id"] == sample_user.id


def test_get_session_context_success(client, sample_user, monkeypatch):
    class OrganizationStub:
        id = 1
        name = "Jane Doe's Workspace"
        slug = "jane-1"
        created_at = sample_user.created_at

    class MembershipStub:
        organization_id = 1
        role = "owner"
        organization = OrganizationStub()

    async def fake_get_by_id(self, user_id):
        return sample_user

    async def fake_list_memberships(self, user_id):
        return [MembershipStub()]

    monkeypatch.setattr(UserService, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(AuthService, "list_memberships", fake_list_memberships)

    response = client.get("/api/v1/auth/context", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["current_organization_id"] == 1
    assert body["current_organization"]["slug"] == "jane-1"
    assert body["memberships"][0]["role"] == "owner"


def test_change_password_success(client, sample_user, monkeypatch):
    async def fake_get_by_id(self, user_id):
        return sample_user

    async def fake_change_password(self, user, current_password, new_password):
        return None

    monkeypatch.setattr(UserService, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(AuthService, "change_password", fake_change_password)

    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "OldPass123", "new_password": "NewPass123"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Password changed successfully"}


def test_logout_success(client, monkeypatch):
    async def fake_revoke(self, token):
        return None

    monkeypatch.setattr(AuthService, "revoke_token", fake_revoke)
    response = client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
