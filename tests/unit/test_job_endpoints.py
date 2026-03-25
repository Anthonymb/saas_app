from types import SimpleNamespace

from app.services.job import JobService


def make_job(job_id=1):
    return SimpleNamespace(
        id=job_id,
        organization_id=1,
        user_id=1,
        type="send_campaign",
        status="pending",
        payload={"campaign_id": 1},
        attempts=0,
        max_attempts=3,
        scheduled_at="2026-01-01T00:00:00Z",
        started_at=None,
        completed_at=None,
        failed_at=None,
        last_error=None,
        created_at="2026-01-01T00:00:00Z",
    )


def test_queue_campaign_send_success(client, monkeypatch):
    async def fake_enqueue(self, organization_id, user_id, campaign_id):
        return make_job(7)

    monkeypatch.setattr(JobService, "enqueue_campaign_send", fake_enqueue)

    response = client.post("/api/v1/campaigns/1/queue-send", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert "Queued campaign send job 7" in response.json()["message"]


def test_list_jobs_success(client, monkeypatch):
    async def fake_list(
        self,
        organization_id,
        page=1,
        page_size=20,
        status=None,
        job_type=None,
    ):
        return [make_job(1), make_job(2)], 2

    monkeypatch.setattr(JobService, "list_by_organization", fake_list)

    response = client.get("/api/v1/jobs", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_jobs_filters_success(client, monkeypatch):
    captured = {}

    async def fake_list(self, organization_id, page=1, page_size=20, status=None, job_type=None):
        captured.update(
            organization_id=organization_id,
            status=status,
            job_type=job_type,
        )
        return [make_job(1)], 1

    monkeypatch.setattr(JobService, "list_by_organization", fake_list)

    response = client.get(
        "/api/v1/jobs?status=pending&type=send_campaign",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert captured["status"] == "pending"
    assert captured["job_type"] == "send_campaign"


def test_job_health_success(client, monkeypatch):
    async def fake_health(self, organization_id):
        return {"pending": 2, "in_progress": 1, "completed": 3, "failed": 0}

    monkeypatch.setattr(JobService, "health_summary", fake_health)

    response = client.get("/api/v1/jobs/health", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["pending"] == 2


def test_get_job_success(client, monkeypatch):
    async def fake_get(self, organization_id, job_id):
        return make_job(job_id)

    monkeypatch.setattr(JobService, "get_by_id", fake_get)

    response = client.get("/api/v1/jobs/1", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_enqueue_payment_webhook_success(client, monkeypatch):
    async def fake_enqueue(self, provider, event_type, provider_ref, metadata=None):
        return make_job(9)

    monkeypatch.setattr(JobService, "enqueue_payment_webhook", fake_enqueue)

    response = client.post(
        "/api/v1/webhooks/payments/stripe",
        json={"event_type": "payment_succeeded", "provider_ref": "stripe-123", "metadata": {"source": "test"}},
    )

    assert response.status_code == 202
    assert "Queued payment webhook job 9" in response.json()["message"]
