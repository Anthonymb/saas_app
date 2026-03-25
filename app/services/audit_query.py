from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditQueryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_organization(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        entity_type: str | None = None,
        user_id: int | None = None,
    ) -> tuple[list[AuditLog], int]:
        offset = (page - 1) * page_size
        filters = [AuditLog.organization_id == organization_id]
        if action:
            filters.append(AuditLog.action == action)
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        total_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(*filters)
        )
        total = total_result.scalar_one()
        result = await self.db.execute(
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
