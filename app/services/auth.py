import re
from typing import Optional

from sqlalchemy import case, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    is_password_strong,
    verify_password,
    verify_token_type,
)
from app.services.audit import AuditService
from app.services.token_session import TokenSessionService
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.token import Token


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)
        self.token_sessions = TokenSessionService(db)

    @staticmethod
    def build_workspace_slug(email: str) -> str:
        local_part = email.split("@", 1)[0].strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", local_part).strip("-")
        if not normalized:
            normalized = "workspace"
        return normalized

    # Helpers
    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_primary_membership(self, user_id: int) -> Optional[Membership]:
        role_priority = case(
            (Membership.role == MembershipRole.OWNER.value, 0),
            (Membership.role == MembershipRole.ADMIN.value, 1),
            else_=2,
        )
        result = await self.db.execute(
            select(Membership)
            .where(Membership.user_id == user_id)
            .order_by(role_priority, Membership.id)
        )
        return result.scalars().first()

    async def list_memberships(self, user_id: int) -> list[Membership]:
        result = await self.db.execute(
            select(Membership)
            .options(selectinload(Membership.organization))
            .where(Membership.user_id == user_id)
            .order_by(Membership.id)
        )
        return list(result.scalars().all())

    # Register
    async def register(
        self,
        email: str,
        full_name: str,
        password: str,
    ) -> User:
        is_strong, error = is_password_strong(password)
        if not is_strong:
            raise BadRequestError(error)

        existing = await self.get_user_by_email(email)
        if existing:
            raise ConflictError("Email already registered")

        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
        )
        self.db.add(user)
        await self.db.flush()

        workspace = Organization(
            name=f"{full_name}'s Workspace",
            slug=f"{self.build_workspace_slug(email)}-{user.id}",
            owner_user_id=user.id,
        )
        self.db.add(workspace)
        await self.db.flush()

        membership = Membership(
            organization_id=workspace.id,
            user_id=user.id,
            role=MembershipRole.OWNER.value,
        )
        self.db.add(membership)
        await self.db.flush()

        await self.audit.log(
            action="user.registered",
            entity_type="user",
            entity_id=str(user.id),
            organization_id=workspace.id,
            user_id=user.id,
            metadata={"email": user.email},
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # Login
    async def login(
        self,
        email: str,
        password: str,
    ) -> User:
        user = await self.get_user_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        return user

    # Token generation
    async def generate_tokens(self, user: User) -> Token:
        primary_membership = await self.get_primary_membership(user.id)
        current_organization_id = primary_membership.organization_id if primary_membership else None
        access_token, access_expires_at, access_jti = create_access_token(
            subject=user.id,
            extra={"current_organization_id": current_organization_id},
        )
        refresh_token, refresh_expires_at, refresh_jti = create_refresh_token(
            subject=user.id,
            extra={"current_organization_id": current_organization_id},
        )
        await self.token_sessions.create(user.id, access_jti, "access", access_expires_at)
        await self.token_sessions.create(user.id, refresh_jti, "refresh", refresh_expires_at)
        await self.db.commit()
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # Refresh token
    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> Token:
        try:
            payload = verify_token_type(refresh_token, "refresh")
            user_id = int(payload["sub"])
            jti = payload.get("jti")
        except Exception:
            raise UnauthorizedError("Invalid or expired refresh token")
        if not jti or await self.token_sessions.is_revoked(jti):
            raise UnauthorizedError("Invalid or expired refresh token")

        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        await self.token_sessions.revoke(jti)
        tokens = await self.generate_tokens(user)
        await self.audit.log(
            action="auth.refresh",
            entity_type="user",
            entity_id=str(user.id),
            organization_id=payload.get("current_organization_id"),
            user_id=user.id,
            metadata={"refresh_jti": jti},
        )
        await self.db.commit()
        return tokens

    async def revoke_token(self, token: str) -> None:
        payload = verify_token_type(token, "access")
        jti = payload.get("jti")
        if not jti:
            raise UnauthorizedError("Invalid access token")
        session = await self.token_sessions.revoke(jti)
        if not session:
            raise UnauthorizedError("Invalid access token")
        await self.audit.log(
            action="auth.logout",
            entity_type="user",
            entity_id=str(session.user_id),
            organization_id=payload.get("current_organization_id"),
            user_id=session.user_id,
            metadata={"access_jti": jti},
        )
        await self.db.commit()

    # Change password
    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestError("Current password is incorrect")

        is_strong, error = is_password_strong(new_password)
        if not is_strong:
            raise BadRequestError(error)

        if verify_password(new_password, user.hashed_password):
            raise BadRequestError("New password must be different from current password")

        user.hashed_password = hash_password(new_password)
        await self.db.flush()
        await self.audit.log(
            action="user.password_changed",
            entity_type="user",
            entity_id=str(user.id),
            user_id=user.id,
        )
        await self.db.commit()
        await self.db.refresh(user)
