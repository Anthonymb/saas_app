from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DatabaseHealthRead(BaseModel):
    status: str
    database: str


class ReadinessRead(BaseModel):
    status: str
    database: str
    queue: str
    pending_jobs: int
    in_progress_jobs: int


class WorkerHealthRead(BaseModel):
    status: str
    pending_jobs: int
    in_progress_jobs: int
    failed_jobs: int
    is_busy: bool
    last_scheduled_at: Optional[datetime] = None
    last_started_at: Optional[datetime] = None
    last_completed_at: Optional[datetime] = None
    last_failed_at: Optional[datetime] = None
