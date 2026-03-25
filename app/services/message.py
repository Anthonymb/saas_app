from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.message import Message
from app.schemas.message import CampaignMessageCreate, MessageUpdate
from app.services.audit import AuditService


class MessageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def list_by_campaign(
        self,
        organization_id: int,
        campaign_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Message], int]:
        offset = (page - 1) * page_size
        campaign = await self._get_campaign(organization_id, campaign_id)

        total_result = await self.db.execute(
            select(func.count(Message.id)).where(Message.campaign_id == campaign.id)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Message)
            .where(Message.campaign_id == campaign.id)
            .order_by(Message.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def create_for_campaign(
        self,
        organization_id: int,
        campaign_id: int,
        data: CampaignMessageCreate,
        user_id: int | None = None,
    ) -> list[Message]:
        campaign = await self._get_campaign(organization_id, campaign_id)
        if not data.contact_ids:
            raise BadRequestError("At least one contact is required")

        contacts_result = await self.db.execute(
            select(Contact).where(
                Contact.organization_id == organization_id,
                Contact.id.in_(data.contact_ids),
            )
        )
        contacts = list(contacts_result.scalars().all())
        if len(contacts) != len(set(data.contact_ids)):
            raise BadRequestError("One or more contacts were not found in this organization")

        messages: list[Message] = []
        for contact in contacts:
            message = Message(
                campaign_id=campaign.id,
                contact_id=contact.id,
                subject=data.subject if data.subject is not None else campaign.subject,
                body=data.body if data.body is not None else campaign.body,
                status=data.status,
            )
            self.db.add(message)
            messages.append(message)

        await self.db.flush()
        await self.audit.log(
            action="message.batch_created",
            entity_type="campaign_message",
            entity_id=str(campaign.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"campaign_id": campaign.id, "message_count": len(messages)},
        )
        await self.db.commit()
        for message in messages:
            await self.db.refresh(message)
        return messages

    async def update(
        self,
        organization_id: int,
        campaign_id: int,
        message_id: int,
        data: MessageUpdate,
        user_id: int | None = None,
    ) -> Message:
        message = await self._get_message(organization_id, campaign_id, message_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(message, field, value)
        await self.db.flush()
        await self.audit.log(
            action="message.updated",
            entity_type="campaign_message",
            entity_id=str(message.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"campaign_id": campaign_id, "updated_fields": sorted(update_data.keys())},
        )
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def _get_campaign(self, organization_id: int, campaign_id: int) -> Campaign:
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.organization_id == organization_id,
                Campaign.id == campaign_id,
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise NotFoundError("Campaign not found")
        return campaign

    async def _get_message(self, organization_id: int, campaign_id: int, message_id: int) -> Message:
        await self._get_campaign(organization_id, campaign_id)
        result = await self.db.execute(
            select(Message)
            .join(Campaign, Campaign.id == Message.campaign_id)
            .where(
                Campaign.organization_id == organization_id,
                Message.campaign_id == campaign_id,
                Message.id == message_id,
            )
        )
        message = result.scalar_one_or_none()
        if not message:
            raise NotFoundError("Message not found")
        return message
