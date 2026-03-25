from types import SimpleNamespace

from app.services.contact import ContactService


def make_contact(contact_id=1):
    return SimpleNamespace(
        id=contact_id,
        organization_id=1,
        user_id=1,
        email=f"contact{contact_id}@example.com",
        first_name="Test",
        last_name="Contact",
        phone=None,
        status="active",
        created_at="2026-01-01T00:00:00Z",
    )


def test_list_contacts_success(client, monkeypatch):
    async def fake_list(
        self,
        organization_id,
        page=1,
        page_size=20,
        email=None,
        status=None,
        search=None,
    ):
        return [make_contact(1), make_contact(2)], 2

    monkeypatch.setattr(ContactService, "list_by_organization", fake_list)

    response = client.get("/api/v1/contacts", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_list_contacts_filters_success(client, monkeypatch):
    captured = {}

    async def fake_list(self, organization_id, page=1, page_size=20, email=None, status=None, search=None):
        captured.update(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            email=email,
            status=status,
            search=search,
        )
        return [make_contact(1)], 1

    monkeypatch.setattr(ContactService, "list_by_organization", fake_list)

    response = client.get(
        "/api/v1/contacts?email=contact@example.com&status=active&search=Test",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert captured["email"] == "contact@example.com"
    assert captured["status"] == "active"
    assert captured["search"] == "Test"


def test_create_contact_success(client, monkeypatch):
    async def fake_create(self, organization_id, user_id, data):
        contact = make_contact(1)
        contact.email = data.email
        contact.first_name = data.first_name
        return contact

    monkeypatch.setattr(ContactService, "create", fake_create)

    response = client.post(
        "/api/v1/contacts",
        json={
            "email": "newcontact@example.com",
            "first_name": "New",
            "last_name": "Contact",
            "phone": "1234567890",
            "status": "active",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "newcontact@example.com"


def test_get_contact_success(client, monkeypatch):
    async def fake_get(self, organization_id, contact_id):
        return make_contact(contact_id)

    monkeypatch.setattr(ContactService, "get_by_id", fake_get)

    response = client.get("/api/v1/contacts/1", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_update_contact_success(client, monkeypatch):
    async def fake_update(self, organization_id, contact_id, data, user_id=None):
        contact = make_contact(contact_id)
        contact.first_name = data.first_name
        return contact

    monkeypatch.setattr(ContactService, "update", fake_update)

    response = client.patch(
        "/api/v1/contacts/1",
        json={"first_name": "Updated"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"


def test_delete_contact_success(client, monkeypatch):
    async def fake_delete(self, organization_id, contact_id, user_id=None):
        return None

    monkeypatch.setattr(ContactService, "delete", fake_delete)

    response = client.delete("/api/v1/contacts/1", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 204
