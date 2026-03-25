from types import SimpleNamespace

from app.services.payment import PaymentService


def make_payment(payment_id=1):
    return SimpleNamespace(
        id=payment_id,
        organization_id=1,
        user_id=1,
        amount=99.99,
        currency="USD",
        status="pending",
        provider="stripe",
        provider_ref=f"ref-{payment_id}",
        provider_metadata=None,
        paid_at=None,
        refunded_at=None,
        created_at="2026-01-01T00:00:00Z",
    )


def test_list_payments_success(client, monkeypatch):
    async def fake_list(
        self,
        organization_id,
        page=1,
        page_size=20,
        status=None,
        provider=None,
        provider_ref=None,
        search=None,
    ):
        return [make_payment(1), make_payment(2)], 2

    monkeypatch.setattr(PaymentService, "list_by_organization", fake_list)

    response = client.get("/api/v1/payments", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_payments_filters_success(client, monkeypatch):
    captured = {}

    async def fake_list(self, organization_id, page=1, page_size=20, status=None, provider=None, provider_ref=None, search=None):
        captured.update(
            organization_id=organization_id,
            status=status,
            provider=provider,
            provider_ref=provider_ref,
            search=search,
        )
        return [make_payment(1)], 1

    monkeypatch.setattr(PaymentService, "list_by_organization", fake_list)

    response = client.get(
        "/api/v1/payments?status=pending&provider=stripe&provider_ref=ref-1&search=USD",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert captured["status"] == "pending"
    assert captured["provider"] == "stripe"
    assert captured["provider_ref"] == "ref-1"
    assert captured["search"] == "USD"


def test_create_payment_success(client, monkeypatch):
    async def fake_create(self, organization_id, user_id, data):
        payment = make_payment(1)
        payment.amount = data.amount
        payment.provider_ref = data.provider_ref
        return payment

    monkeypatch.setattr(PaymentService, "create", fake_create)

    response = client.post(
        "/api/v1/payments",
        json={
            "amount": 150.0,
            "currency": "USD",
            "provider": "stripe",
            "provider_ref": "stripe-123",
            "status": "pending",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 201
    assert response.json()["amount"] == 150.0


def test_get_payment_success(client, monkeypatch):
    async def fake_get(self, organization_id, payment_id):
        return make_payment(payment_id)

    monkeypatch.setattr(PaymentService, "get_by_id", fake_get)

    response = client.get("/api/v1/payments/1", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_update_payment_success(client, monkeypatch):
    async def fake_update(self, organization_id, payment_id, data, user_id=None):
        payment = make_payment(payment_id)
        payment.status = data.status
        return payment

    monkeypatch.setattr(PaymentService, "update", fake_update)

    response = client.patch(
        "/api/v1/payments/1",
        json={"status": "succeeded"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"


def test_delete_payment_success(client, monkeypatch):
    async def fake_delete(self, organization_id, payment_id, user_id=None):
        return None

    monkeypatch.setattr(PaymentService, "delete", fake_delete)

    response = client.delete("/api/v1/payments/1", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 204
