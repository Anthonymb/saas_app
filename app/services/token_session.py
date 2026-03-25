from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_session import TokenSession


class TokenSessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: int, jti: str, token_type: str, expires_at: datetime) -> TokenSession:
        session = TokenSession(
            user_id=user_id,
            jti=jti,
            token_type=token_type,
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_jti(self, jti: str) -> Optional[TokenSession]:
        result = await self.db.execute(select(TokenSession).where(TokenSession.jti == jti))
        return result.scalar_one_or_none()

    async def is_revoked(self, jti: str) -> bool:
        session = await self.get_by_jti(jti)
        return bool(session and session.revoked_at is not None)

    async def revoke(self, jti: str) -> Optional[TokenSession]:
        session = await self.get_by_jti(jti)
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            await self.db.flush()
        return session
