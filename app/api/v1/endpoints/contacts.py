from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_organization_id, get_current_user_id, get_db
from app.schemas.common import PaginatedResponse
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from app.services.contact import ContactService

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("", response_model=PaginatedResponse[ContactRead])
async def list_contacts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    email: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = ContactService(db)
    items, total = await svc.list_by_organization(
        organization_id,
        page=page,
        page_size=page_size,
        email=email,
        status=status,
        search=search,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[ContactRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = ContactService(db)
    return await svc.create(organization_id=organization_id, user_id=user_id, data=payload)


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(
    contact_id: int,
    organization_id: int = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db),
):
    svc = ContactService(db)
    contact = await svc.get_by_id(organization_id, contact_id)
    if not contact:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = ContactService(db)
    return await svc.update(
        organization_id=organization_id,
        contact_id=contact_id,
        data=payload,
        user_id=user_id,
    )


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    organization_id: int = Depends(get_current_organization_id),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = ContactService(db)
    await svc.delete(organization_id=organization_id, contact_id=contact_id, user_id=user_id)
