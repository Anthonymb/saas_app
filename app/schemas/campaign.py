from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CampaignBase(BaseModel):
    name: str
    subject: Optional[str] = None
    body: Optional[str] = None
    channel: str = "email"


class CampaignCreate(CampaignBase):
    status: str = "draft"
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    channel: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None


class CampaignAnalyticsRead(BaseModel):
    total_messages: int = 0
    queued: int = 0
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    bounced: int = 0
    failed: int = 0


class CampaignRead(CampaignBase):
    id: int
    organization_id: int
    user_id: int
    status: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    analytics: CampaignAnalyticsRead = Field(default_factory=CampaignAnalyticsRead)
    model_config = {"from_attributes": True}
