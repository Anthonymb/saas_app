from types import SimpleNamespace

from app.services.audit_query import AuditQueryService


def make_audit_log(log_id=1):
    return SimpleNamespace(
        id=log_id,
        organization_id=1,
        user_id=1,
        action="contact.created",
        entity_type="contact",
        entity_id="1",
        event_data={"email": "contact@example.com"},
        created_at="2026-01-01T00:00:00Z",
    )


def test_list_audit_logs_success(client, monkeypatch):
    async def fake_list(self, organization_id, page=1, page_size=50, action=None, entity_type=None, user_id=None):
        return [make_audit_log(1), make_audit_log(2)], 2

    monkeypatch.setattr(AuditQueryService, "list_by_organization", fake_list)

    response = client.get("/api/v1/audit-logs", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_audit_logs_filters_success(client, monkeypatch):
    captured = {}

    async def fake_list(self, organization_id, page=1, page_size=50, action=None, entity_type=None, user_id=None):
        captured.update(
            organization_id=organization_id,
            action=action,
            entity_type=entity_type,
            user_id=user_id,
        )
        return [make_audit_log(1)], 1

    monkeypatch.setattr(AuditQueryService, "list_by_organization", fake_list)

    response = client.get(
        "/api/v1/audit-logs?action=contact.created&entity_type=contact&user_id=1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert captured["action"] == "contact.created"
    assert captured["entity_type"] == "contact"
    assert captured["user_id"] == 1
