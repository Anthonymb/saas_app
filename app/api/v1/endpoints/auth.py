from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.dependencies import get_current_organization_id, get_current_user_id, get_db
from app.core.dependencies import oauth2_scheme
from app.schemas.auth import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.session import SessionContextRead
from app.schemas.token import Token
from app.schemas.user import UserRead
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


# Register
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with email, full name and password. Password must be at least 8 characters with uppercase, lowercase and a number.",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    user = await svc.register(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
    )
    return user


# Login
@router.post(
    "/login",
    response_model=Token,
    summary="Login with email and password",
    description="Authenticates a user and returns JWT access and refresh tokens.",
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    user = await svc.login(
        email=form.username,
        password=form.password,
    )
    return await svc.generate_tokens(user)


# Refresh token
@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access and refresh token pair.",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    tokens = await svc.refresh_access_token(payload.refresh_token)
    return tokens


@router.get(
    "/context",
    response_model=SessionContextRead,
    summary="Get current session context",
    description="Returns the authenticated user together with current organization and memberships.",
)
async def get_session_context(
    user_id: int = Depends(get_current_user_id),
    current_organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc_user = UserService(db)
    svc_auth = AuthService(db)

    user = await svc_user.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")

    memberships = await svc_auth.list_memberships(user_id)
    current_membership = next(
        (membership for membership in memberships if membership.organization_id == current_organization_id),
        None,
    )
    if not current_membership:
        raise NotFoundError("Organization membership not found")

    return SessionContextRead(
        user=UserRead.model_validate(user),
        current_organization_id=current_organization_id,
        current_organization=current_membership.organization,
        memberships=memberships,
    )


# Get current user
@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


# Change password
@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password. Requires the current password for verification.",
)
async def change_password(
    payload: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc_user = UserService(db)
    svc_auth = AuthService(db)

    user = await svc_user.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")

    await svc_auth.change_password(
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )

    return MessageResponse(message="Password changed successfully")


# Logout
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Logs out the current user. The client should delete the stored tokens.",
)
async def logout(
    _user_id: int = Depends(get_current_user_id),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    await svc.revoke_token(token)
    return MessageResponse(message="Logged out successfully")
