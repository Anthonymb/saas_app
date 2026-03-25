from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.schemas.token import TokenPayload
from app.services.token_session import TokenSessionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a database session for each request.
    Transaction boundaries are handled explicitly by the service layer.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# Auth guard
async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    Validates the JWT access token and returns the user ID.
    Add this as a dependency to any protected route:
        user_id: int = Depends(get_current_user_id)
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)

        # Make sure it's an access token not a refresh token
        if payload.get("type") != "access":
            raise credentials_exc

        token_data = TokenPayload(**payload)
        async with AsyncSessionLocal() as session:
            token_sessions = TokenSessionService(session)
            if not token_data.jti or await token_sessions.is_revoked(token_data.jti):
                raise credentials_exc

    except JWTError as exc:
        if "expired" in str(exc).lower():
            raise expired_exc
        raise credentials_exc
    except ValueError:
        raise credentials_exc

    return int(token_data.sub)


async def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        token_data = TokenPayload(**payload)
        async with AsyncSessionLocal() as session:
            token_sessions = TokenSessionService(session)
            if not token_data.jti or await token_sessions.is_revoked(token_data.jti):
                raise credentials_exc
        return token_data
    except JWTError as exc:
        if "expired" in str(exc).lower():
            raise expired_exc
        raise credentials_exc
    except ValueError:
        raise credentials_exc


async def get_current_organization_id(
    token_payload: TokenPayload = Depends(get_current_token_payload),
) -> int:
    if token_payload.current_organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not resolve organization context",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_payload.current_organization_id
