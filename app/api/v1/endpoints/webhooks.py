from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.common import MessageResponse
from app.schemas.webhook import PaymentWebhookRequest
from app.services.job import JobService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/payments/{provider}", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_payment_webhook(
    provider: str,
    payload: PaymentWebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = JobService(db)
    job = await svc.enqueue_payment_webhook(
        provider=provider,
        event_type=payload.event_type,
        provider_ref=payload.provider_ref,
        metadata=payload.metadata,
    )
    return MessageResponse(message=f"Queued payment webhook job {job.id}")
