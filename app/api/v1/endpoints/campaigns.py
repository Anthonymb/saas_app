from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_organization_id, get_current_user_id, get_db
from app.core.exceptions import NotFoundError
from app.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.message import CampaignMessageCreate, MessageRead, MessageUpdate
from app.services.campaign import CampaignService
from app.services.job import JobService
from app.services.message import MessageService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=PaginatedResponse[CampaignRead])
async def list_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    search: str | None = Query(default=None),
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = CampaignService(db)
    items, total = await svc.list_by_organization(
        organization_id,
        page=page,
        page_size=page_size,
        status=status,
        channel=channel,
        search=search,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[CampaignRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = CampaignService(db)
    return await svc.create(organization_id=organization_id, user_id=user_id, data=payload)


@router.get("/{campaign_id}", response_model=CampaignRead)
async def get_campaign(
    campaign_id: int,
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = CampaignService(db)
    campaign = await svc.get_by_id(organization_id, campaign_id)
    if not campaign:
        raise NotFoundError("Campaign not found")
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignRead)
async def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = CampaignService(db)
    return await svc.update(
        organization_id=organization_id,
        campaign_id=campaign_id,
        data=payload,
        user_id=user_id,
    )


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = CampaignService(db)
    await svc.delete(organization_id=organization_id, campaign_id=campaign_id, user_id=user_id)


@router.post("/{campaign_id}/queue-send", response_model=MessageResponse)
async def queue_campaign_send(
    campaign_id: int,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = JobService(db)
    job = await svc.enqueue_campaign_send(
        organization_id=organization_id,
        user_id=user_id,
        campaign_id=campaign_id,
    )
    return MessageResponse(message=f"Queued campaign send job {job.id}")


@router.get("/{campaign_id}/messages", response_model=PaginatedResponse[MessageRead])
async def list_campaign_messages(
    campaign_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    items, total = await svc.list_by_campaign(organization_id, campaign_id, page=page, page_size=page_size)
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[MessageRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/{campaign_id}/messages", response_model=list[MessageRead], status_code=status.HTTP_201_CREATED)
async def create_campaign_messages(
    campaign_id: int,
    payload: CampaignMessageCreate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    return await svc.create_for_campaign(
        organization_id=organization_id,
        campaign_id=campaign_id,
        data=payload,
        user_id=user_id,
    )


@router.patch("/{campaign_id}/messages/{message_id}", response_model=MessageRead)
async def update_campaign_message(
    campaign_id: int,
    message_id: int,
    payload: MessageUpdate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    return await svc.update(
        organization_id=organization_id,
        campaign_id=campaign_id,
        message_id=message_id,
        data=payload,
        user_id=user_id,
    )
