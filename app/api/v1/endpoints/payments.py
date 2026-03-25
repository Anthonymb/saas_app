from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_organization_id, get_current_user_id, get_db
from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.services.payment import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", response_model=PaginatedResponse[PaymentRead])
async def list_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    provider_ref: str | None = Query(default=None),
    search: str | None = Query(default=None),
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PaymentService(db)
    items, total = await svc.list_by_organization(
        organization_id,
        page=page,
        page_size=page_size,
        status=status,
        provider=provider,
        provider_ref=provider_ref,
        search=search,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[PaymentRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PaymentService(db)
    return await svc.create(organization_id=organization_id, user_id=user_id, data=payload)


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: int,
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PaymentService(db)
    payment = await svc.get_by_id(organization_id, payment_id)
    if not payment:
        raise NotFoundError("Payment not found")
    return payment


@router.patch("/{payment_id}", response_model=PaymentRead)
async def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PaymentService(db)
    return await svc.update(
        organization_id=organization_id,
        payment_id=payment_id,
        data=payload,
        user_id=user_id,
    )


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PaymentService(db)
    await svc.delete(organization_id=organization_id, payment_id=payment_id, user_id=user_id)
