from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobRead(BaseModel):
    id: int
    organization_id: int
    user_id: int
    type: str
    status: str
    payload: dict
    attempts: int
    max_attempts: int
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class JobHealthRead(BaseModel):
    pending: int
    in_progress: int
    completed: int
    failed: int
