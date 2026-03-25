from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaymentBase(BaseModel):
    amount: float
    currency: str = "USD"
    provider: str = "stripe"
    provider_ref: Optional[str] = None
    provider_metadata: Optional[str] = None


class PaymentCreate(PaymentBase):
    status: str = "pending"
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None


class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    provider: Optional[str] = None
    provider_ref: Optional[str] = None
    provider_metadata: Optional[str] = None
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None


class PaymentRead(PaymentBase):
    id: int
    organization_id: int
    user_id: int
    status: str
    paid_at: Optional[datetime]
    refunded_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}
