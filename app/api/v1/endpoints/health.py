from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.health import DatabaseHealthRead, ReadinessRead, WorkerHealthRead
from app.services.job import JobService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    return {"status": "ok"}


@router.get("/liveness")
async def liveness_check():
    return {"status": "ok"}


@router.get("/db", response_model=DatabaseHealthRead)
async def db_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "unavailable"},
        )


@router.get("/readiness", response_model=ReadinessRead)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    job_service = JobService(db)
    try:
        await db.execute(text("SELECT 1"))
        counts = await job_service.global_health_summary()
        return ReadinessRead(
            status="ok",
            database="connected",
            queue="available",
            pending_jobs=counts["pending"],
            in_progress_jobs=counts["in_progress"],
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "unavailable",
                "queue": "unknown",
                "pending_jobs": 0,
                "in_progress_jobs": 0,
            },
        )


@router.get("/worker", response_model=WorkerHealthRead)
async def worker_health(db: AsyncSession = Depends(get_db)):
    svc = JobService(db)
    return WorkerHealthRead(**await svc.worker_status())
