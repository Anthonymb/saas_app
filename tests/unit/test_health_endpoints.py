from datetime import datetime, timezone

from app.services.job import JobService


def test_health_liveness_success(client):
    response = client.get("/api/v1/health/liveness")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_success(client):
    response = client.get("/api/v1/health/db")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_health_readiness_success(client, monkeypatch):
    async def fake_global_health_summary(self):
        return {"pending": 3, "in_progress": 1, "completed": 5, "failed": 0}

    monkeypatch.setattr(JobService, "global_health_summary", fake_global_health_summary)

    response = client.get("/api/v1/health/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["queue"] == "available"
    assert body["pending_jobs"] == 3
    assert body["in_progress_jobs"] == 1


def test_health_worker_success(client, monkeypatch):
    async def fake_worker_status(self):
        return {
            "status": "ok",
            "pending_jobs": 2,
            "in_progress_jobs": 1,
            "failed_jobs": 0,
            "is_busy": True,
            "last_scheduled_at": datetime.now(timezone.utc),
            "last_started_at": datetime.now(timezone.utc),
            "last_completed_at": datetime.now(timezone.utc),
            "last_failed_at": None,
        }

    monkeypatch.setattr(JobService, "worker_status", fake_worker_status)

    response = client.get("/api/v1/health/worker")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["pending_jobs"] == 2
    assert body["in_progress_jobs"] == 1
    assert body["is_busy"] is True
