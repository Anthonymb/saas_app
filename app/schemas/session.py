from pydantic import BaseModel

from app.schemas.organization import MembershipRead, OrganizationRead
from app.schemas.user import UserRead


class SessionContextRead(BaseModel):
    user: UserRead
    current_organization_id: int
    current_organization: OrganizationRead
    memberships: list[MembershipRead]
