from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_organization_id, get_current_user_id, get_db
from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.job import JobHealthRead, JobRead
from app.schemas.common import MessageResponse
from app.services.job import JobService
from app.workers.campaign_worker import run_once

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=PaginatedResponse[JobRead])
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None, alias="type"),
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = JobService(db)
    items, total = await svc.list_by_organization(
        organization_id,
        page=page,
        page_size=page_size,
        status=status,
        job_type=job_type,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[JobRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/health", response_model=JobHealthRead)
async def get_job_health(
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = JobService(db)
    counts = await svc.health_summary(organization_id)
    return JobHealthRead(**counts)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: int,
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = JobService(db)
    job = await svc.get_by_id(organization_id, job_id)
    if not job:
        raise NotFoundError("Job not found")
    return job


@router.post("/run-once", response_model=MessageResponse)
async def run_jobs_once(
    _user_id: int = Depends(get_current_user_id),
):
    processed = await run_once()
    if processed:
        return MessageResponse(message="Processed one queued job")
    return MessageResponse(message="No queued jobs available")
