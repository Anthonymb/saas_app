from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CampaignMessageCreate(BaseModel):
    contact_ids: list[int]
    subject: Optional[str] = None
    body: Optional[str] = None
    status: str = "pending"


class MessageUpdate(BaseModel):
    status: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None


class MessageRead(BaseModel):
    id: int
    campaign_id: int
    contact_id: int
    subject: Optional[str]
    body: Optional[str]
    status: str
    error_message: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    bounced_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}
