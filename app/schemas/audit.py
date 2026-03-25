from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    organization_id: Optional[int]
    user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[str]
    event_data: dict
    created_at: datetime
    model_config = {"from_attributes": True}
