from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.campaign import Campaign
from app.models.job import Job, JobStatus, JobType
from app.models.payment import Payment
from app.services.audit import AuditService


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def list_by_organization(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        job_type: str | None = None,
    ) -> tuple[list[Job], int]:
        offset = (page - 1) * page_size
        filters = [Job.organization_id == organization_id]
        if status:
            filters.append(Job.status == status)
        if job_type:
            filters.append(Job.type == job_type)
        total_result = await self.db.execute(
            select(func.count(Job.id)).where(*filters)
        )
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(Job)
            .where(*filters)
            .order_by(Job.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, organization_id: int, job_id: int) -> Optional[Job]:
        result = await self.db.execute(
            select(Job).where(Job.organization_id == organization_id, Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def health_summary(self, organization_id: int) -> dict[str, int]:
        result = await self.db.execute(
            select(Job.status, func.count(Job.id))
            .where(Job.organization_id == organization_id)
            .group_by(Job.status)
        )
        counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        for status, count in result.all():
            counts[status] = count
        return counts

    async def global_health_summary(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Job.status, func.count(Job.id))
            .group_by(Job.status)
        )
        counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        for status, count in result.all():
            counts[status] = count
        return counts

    async def worker_status(self) -> dict[str, object]:
        counts = await self.global_health_summary()
        result = await self.db.execute(
            select(
                func.max(Job.scheduled_at),
                func.max(Job.started_at),
                func.max(Job.completed_at),
                func.max(Job.failed_at),
            )
        )
        last_scheduled_at, last_started_at, last_completed_at, last_failed_at = result.one()
        is_busy = counts["in_progress"] > 0
        is_healthy = counts["failed"] == 0 or counts["completed"] > 0 or is_busy
        return {
            "status": "ok" if is_healthy else "warning",
            "pending_jobs": counts["pending"],
            "in_progress_jobs": counts["in_progress"],
            "failed_jobs": counts["failed"],
            "last_scheduled_at": last_scheduled_at,
            "last_started_at": last_started_at,
            "last_completed_at": last_completed_at,
            "last_failed_at": last_failed_at,
            "is_busy": is_busy,
        }

    async def enqueue_campaign_send(self, organization_id: int, user_id: int, campaign_id: int) -> Job:
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.organization_id == organization_id,
                Campaign.id == campaign_id,
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise NotFoundError("Campaign not found")

        campaign.status = "scheduled"
        job = Job(
            organization_id=organization_id,
            user_id=user_id,
            type=JobType.SEND_CAMPAIGN.value,
            status=JobStatus.PENDING.value,
            payload={"campaign_id": campaign_id},
            scheduled_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()
        await self.audit.log(
            action="job.enqueued",
            entity_type="job",
            entity_id=str(job.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"job_type": job.type, "campaign_id": campaign_id},
        )
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def enqueue_payment_webhook(
        self,
        provider: str,
        event_type: str,
        provider_ref: str,
        metadata: dict | None = None,
    ) -> Job:
        result = await self.db.execute(
            select(Payment).where(Payment.provider_ref == provider_ref)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundError("Payment not found for webhook provider reference")

        job = Job(
            organization_id=payment.organization_id,
            user_id=payment.user_id,
            type=JobType.PROCESS_PAYMENT_WEBHOOK.value,
            status=JobStatus.PENDING.value,
            payload={
                "provider": provider,
                "event_type": event_type,
                "provider_ref": provider_ref,
                "metadata": metadata or {},
            },
            scheduled_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()
        await self.audit.log(
            action="job.enqueued",
            entity_type="job",
            entity_id=str(job.id),
            organization_id=payment.organization_id,
            user_id=payment.user_id,
            metadata={"job_type": job.type, "provider": provider, "provider_ref": provider_ref, "event_type": event_type},
        )
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def claim_next_job(self) -> Optional[Job]:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Job)
            .where(
                Job.status == JobStatus.PENDING.value,
                Job.scheduled_at <= now,
            )
            .order_by(Job.scheduled_at, Job.id)
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if not job:
            return None

        job.status = JobStatus.IN_PROGRESS.value
        job.started_at = now
        job.attempts += 1
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def mark_completed(self, job: Job) -> Job:
        job.status = JobStatus.COMPLETED.value
        job.completed_at = datetime.now(timezone.utc)
        job.last_error = None
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def mark_failed(self, job: Job, error: str) -> Job:
        now = datetime.now(timezone.utc)
        job.last_error = error[:1000]
        if job.attempts >= job.max_attempts:
            job.status = JobStatus.FAILED.value
            job.failed_at = now
        else:
            job.status = JobStatus.PENDING.value
            job.scheduled_at = now + timedelta(minutes=2 ** max(job.attempts - 1, 0))
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(job)
        return job
