from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.campaign import Campaign
from app.models.message import Message
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.services.audit import AuditService


class CampaignService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    @staticmethod
    def _empty_analytics() -> dict[str, int]:
        return {
            "total_messages": 0,
            "queued": 0,
            "sent": 0,
            "delivered": 0,
            "opened": 0,
            "clicked": 0,
            "bounced": 0,
            "failed": 0,
        }

    async def _attach_analytics(self, campaigns: list[Campaign]) -> list[Campaign]:
        if not campaigns:
            return campaigns

        campaign_ids = [campaign.id for campaign in campaigns]
        counts_result = await self.db.execute(
            select(Message.campaign_id, Message.status, func.count(Message.id))
            .where(Message.campaign_id.in_(campaign_ids))
            .group_by(Message.campaign_id, Message.status)
        )
        counts_by_campaign = {
            campaign.id: self._empty_analytics()
            for campaign in campaigns
        }

        for campaign_id, message_status, count in counts_result.all():
            analytics = counts_by_campaign[campaign_id]
            analytics["total_messages"] += count
            if message_status == "queued":
                analytics["queued"] = count
            elif message_status == "sent":
                analytics["sent"] = count
            elif message_status == "delivered":
                analytics["delivered"] = count
            elif message_status == "opened":
                analytics["opened"] = count
            elif message_status == "clicked":
                analytics["clicked"] = count
            elif message_status == "bounced":
                analytics["bounced"] = count
            elif message_status == "failed":
                analytics["failed"] = count

        for campaign in campaigns:
            setattr(campaign, "analytics", counts_by_campaign[campaign.id])

        return campaigns

    async def list_by_organization(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        channel: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Campaign], int]:
        offset = (page - 1) * page_size
        filters = [Campaign.organization_id == organization_id]
        if status:
            filters.append(Campaign.status == status)
        if channel:
            filters.append(Campaign.channel == channel)
        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Campaign.name.ilike(term),
                    Campaign.subject.ilike(term),
                )
            )

        total_result = await self.db.execute(
            select(func.count(Campaign.id)).where(*filters)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Campaign)
            .where(*filters)
            .order_by(Campaign.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        campaigns = list(result.scalars().all())
        await self._attach_analytics(campaigns)
        return campaigns, total

    async def get_by_id(self, organization_id: int, campaign_id: int) -> Optional[Campaign]:
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.organization_id == organization_id,
                Campaign.id == campaign_id,
            )
        )
        campaign = result.scalar_one_or_none()
        if campaign:
            await self._attach_analytics([campaign])
        return campaign

    async def create(self, organization_id: int, user_id: int, data: CampaignCreate) -> Campaign:
        campaign = Campaign(
            organization_id=organization_id,
            user_id=user_id,
            name=data.name,
            subject=data.subject,
            body=data.body,
            status=data.status,
            channel=data.channel,
            scheduled_at=data.scheduled_at,
        )
        self.db.add(campaign)
        await self.db.flush()
        await self.audit.log(
            action="campaign.created",
            entity_type="campaign",
            entity_id=str(campaign.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"name": campaign.name, "status": campaign.status, "channel": campaign.channel},
        )
        await self.db.commit()
        await self.db.refresh(campaign)
        setattr(campaign, "analytics", self._empty_analytics())
        return campaign

    async def update(
        self,
        organization_id: int,
        campaign_id: int,
        data: CampaignUpdate,
        user_id: int | None = None,
    ) -> Campaign:
        campaign = await self.get_by_id(organization_id, campaign_id)
        if not campaign:
            raise NotFoundError("Campaign not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        await self.db.flush()
        await self.audit.log(
            action="campaign.updated",
            entity_type="campaign",
            entity_id=str(campaign.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"updated_fields": sorted(update_data.keys())},
        )
        await self.db.commit()
        await self.db.refresh(campaign)
        await self._attach_analytics([campaign])
        return campaign

    async def delete(self, organization_id: int, campaign_id: int, user_id: int | None = None) -> None:
        campaign = await self.get_by_id(organization_id, campaign_id)
        if not campaign:
            raise NotFoundError("Campaign not found")

        await self.audit.log(
            action="campaign.deleted",
            entity_type="campaign",
            entity_id=str(campaign.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"name": campaign.name},
        )
        await self.db.delete(campaign)
        await self.db.flush()
        await self.db.commit()
