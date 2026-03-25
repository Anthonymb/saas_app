from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        organization_id: int | None = None,
        user_id: int | None = None,
        metadata: dict | None = None,
        commit: bool = False,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            organization_id=organization_id,
            user_id=user_id,
            event_data=metadata or {},
        )
        self.db.add(entry)
        await self.db.flush()
        if commit:
            await self.db.commit()
            await self.db.refresh(entry)
        return entry
