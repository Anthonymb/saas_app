import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.logging import configure_logging
from app.db.session import AsyncSessionLocal
from app.models.campaign import Campaign
from app.models.job import JobType
from app.models.message import Message
from app.models.payment import Payment
from app.services.job import JobService

configure_logging()
logger = logging.getLogger("worker.campaign")


async def handle_campaign_send(job) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Campaign).where(Campaign.id == job.payload["campaign_id"])
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found for queued job")

        campaign.status = "sending"
        await db.flush()

        messages_result = await db.execute(
            select(Message).where(Message.campaign_id == campaign.id)
        )
        messages = list(messages_result.scalars().all())
        sent_at = datetime.now(timezone.utc)
        for message in messages:
            message.status = "sent"
            message.sent_at = sent_at

        campaign.status = "sent"
        campaign.sent_at = sent_at
        await db.commit()


async def handle_payment_webhook(job) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Payment).where(Payment.provider_ref == job.payload["provider_ref"])
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise ValueError("Payment not found for queued webhook")

        event_type = job.payload["event_type"]
        if event_type == "payment_succeeded":
            payment.status = "succeeded"
            payment.paid_at = datetime.now(timezone.utc)
        elif event_type == "payment_failed":
            payment.status = "failed"
        elif event_type == "payment_refunded":
            payment.status = "refunded"
            payment.refunded_at = datetime.now(timezone.utc)
        else:
            raise ValueError(f"Unsupported payment webhook event type: {event_type}")

        payment.provider_metadata = str(job.payload.get("metadata", {}))
        await db.commit()


async def run_once() -> bool:
    async with AsyncSessionLocal() as db:
        svc = JobService(db)
        job = await svc.claim_next_job()
        if not job:
            return False

        try:
            if job.type == JobType.SEND_CAMPAIGN.value:
                await handle_campaign_send(job)
            elif job.type == JobType.PROCESS_PAYMENT_WEBHOOK.value:
                await handle_payment_webhook(job)
            else:
                raise ValueError(f"Unsupported job type: {job.type}")
        except Exception as exc:
            await svc.mark_failed(job, str(exc))
            logger.exception("Job failed", extra={"request_id": "-", "job_id": job.id})
            return True

        await svc.mark_completed(job)
        logger.info("Job completed", extra={"request_id": "-", "job_id": job.id})
        return True


async def run_forever(poll_interval_seconds: int = 5) -> None:
    logger.info("Campaign worker started", extra={"request_id": "-"})
    while True:
        processed = await run_once()
        if not processed:
            await asyncio.sleep(poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_forever())
