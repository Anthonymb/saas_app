from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_organization_id, get_db
from app.schemas.audit import AuditLogRead
from app.schemas.common import PaginatedResponse
from app.services.audit_query import AuditQueryService

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", response_model=PaginatedResponse[AuditLogRead])
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = AuditQueryService(db)
    items, total = await svc.list_by_organization(
        organization_id,
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
        user_id=user_id,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[AuditLogRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
