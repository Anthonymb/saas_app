from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class ContactCreate(ContactBase):
    status: str = "active"


class ContactUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class ContactRead(ContactBase):
    id: int
    organization_id: int
    user_id: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
