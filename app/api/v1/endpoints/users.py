from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError
from app.core.dependencies import get_current_user_id, get_db
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    return user

@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    if payload.email and payload.email != user.email:
        if await svc.get_by_email(payload.email):
            raise ConflictError("Email already in use")
    return await svc.update(user, payload)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    await svc.delete(user)
