from types import SimpleNamespace

from app.services.campaign import CampaignService
from app.services.message import MessageService


def make_campaign(campaign_id=1):
    return SimpleNamespace(
        id=campaign_id,
        organization_id=1,
        user_id=1,
        name=f"Campaign {campaign_id}",
        subject="Subject",
        body="Body",
        status="draft",
        channel="email",
        scheduled_at=None,
        sent_at=None,
        created_at="2026-01-01T00:00:00Z",
        analytics={
            "total_messages": 2,
            "queued": 1,
            "sent": 1,
            "delivered": 0,
            "opened": 0,
            "clicked": 0,
            "bounced": 0,
            "failed": 0,
        },
    )


def make_message(message_id=1):
    return SimpleNamespace(
        id=message_id,
        campaign_id=1,
        contact_id=message_id,
        subject="Subject",
        body="Body",
        status="pending",
        error_message=None,
        sent_at=None,
        delivered_at=None,
        opened_at=None,
        clicked_at=None,
        bounced_at=None,
        created_at="2026-01-01T00:00:00Z",
    )


def test_list_campaigns_success(client, monkeypatch):
    async def fake_list(
        self,
        organization_id,
        page=1,
        page_size=20,
        status=None,
        channel=None,
        search=None,
    ):
        return [make_campaign(1), make_campaign(2)], 2

    monkeypatch.setattr(CampaignService, "list_by_organization", fake_list)

    response = client.get("/api/v1/campaigns", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["analytics"]["total_messages"] == 2


def test_list_campaigns_filters_success(client, monkeypatch):
    captured = {}

    async def fake_list(self, organization_id, page=1, page_size=20, status=None, channel=None, search=None):
        captured.update(
            organization_id=organization_id,
            status=status,
            channel=channel,
            search=search,
        )
        return [make_campaign(1)], 1

    monkeypatch.setattr(CampaignService, "list_by_organization", fake_list)

    response = client.get(
        "/api/v1/campaigns?status=draft&channel=email&search=Launch",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert captured["status"] == "draft"
    assert captured["channel"] == "email"
    assert captured["search"] == "Launch"


def test_create_campaign_success(client, monkeypatch):
    async def fake_create(self, organization_id, user_id, data):
        campaign = make_campaign(1)
        campaign.name = data.name
        return campaign

    monkeypatch.setattr(CampaignService, "create", fake_create)

    response = client.post(
        "/api/v1/campaigns",
        json={"name": "Launch", "subject": "Hello", "body": "World", "channel": "email", "status": "draft"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Launch"
    assert response.json()["analytics"]["total_messages"] == 2


def test_create_campaign_messages_success(client, monkeypatch):
    async def fake_create_messages(self, organization_id, campaign_id, data, user_id=None):
        return [make_message(1), make_message(2)]

    monkeypatch.setattr(MessageService, "create_for_campaign", fake_create_messages)

    response = client.post(
        "/api/v1/campaigns/1/messages",
        json={"contact_ids": [1, 2]},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 201
    assert len(response.json()) == 2


def test_list_campaign_messages_success(client, monkeypatch):
    async def fake_list_messages(self, organization_id, campaign_id, page=1, page_size=50):
        return [make_message(1)], 1

    monkeypatch.setattr(MessageService, "list_by_campaign", fake_list_messages)

    response = client.get("/api/v1/campaigns/1/messages", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_campaign_message_success(client, monkeypatch):
    async def fake_update(self, organization_id, campaign_id, message_id, data, user_id=None):
        message = make_message(message_id)
        message.status = data.status
        return message

    monkeypatch.setattr(MessageService, "update", fake_update)

    response = client.patch(
        "/api/v1/campaigns/1/messages/1",
        json={"status": "sent"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
