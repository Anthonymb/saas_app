from app.services.user import UserService


def test_get_user_me_success(client, sample_user, monkeypatch):
    async def fake_get_by_id(self, user_id):
        return sample_user

    monkeypatch.setattr(UserService, "get_by_id", fake_get_by_id)

    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["email"] == sample_user.email


def test_update_user_me_success(client, sample_user, monkeypatch):
    async def fake_get_by_id(self, user_id):
        return sample_user

    async def fake_get_by_email(self, email):
        return None

    async def fake_update(self, user, data):
        sample_user.full_name = data.full_name
        return sample_user

    monkeypatch.setattr(UserService, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(UserService, "get_by_email", fake_get_by_email)
    monkeypatch.setattr(UserService, "update", fake_update)

    response = client.patch(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_delete_user_me_success(client, sample_user, monkeypatch):
    async def fake_get_by_id(self, user_id):
        return sample_user

    async def fake_delete(self, user):
        return None

    monkeypatch.setattr(UserService, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(UserService, "delete", fake_delete)

    response = client.delete("/api/v1/users/me", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 204
