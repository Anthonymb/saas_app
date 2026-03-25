from datetime import datetime

from pydantic import BaseModel


class OrganizationRead(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime
    model_config = {"from_attributes": True}


class MembershipRead(BaseModel):
    organization_id: int
    role: str
    organization: OrganizationRead
    model_config = {"from_attributes": True}
