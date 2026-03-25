from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate
from app.services.audit import AuditService


class ContactService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def list_by_organization(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
        email: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Contact], int]:
        offset = (page - 1) * page_size
        filters = [Contact.organization_id == organization_id]
        if email:
            filters.append(Contact.email.ilike(f"%{email}%"))
        if status:
            filters.append(Contact.status == status)
        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Contact.email.ilike(term),
                    Contact.first_name.ilike(term),
                    Contact.last_name.ilike(term),
                )
            )

        total_result = await self.db.execute(
            select(func.count(Contact.id)).where(*filters)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Contact)
            .where(*filters)
            .order_by(Contact.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, organization_id: int, contact_id: int) -> Optional[Contact]:
        result = await self.db.execute(
            select(Contact).where(
                Contact.organization_id == organization_id,
                Contact.id == contact_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, organization_id: int, email: str) -> Optional[Contact]:
        result = await self.db.execute(
            select(Contact).where(
                Contact.organization_id == organization_id,
                Contact.email == email,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, organization_id: int, user_id: int, data: ContactCreate) -> Contact:
        existing = await self.get_by_email(organization_id, data.email)
        if existing:
            raise ConflictError("Contact email already exists in this organization")

        contact = Contact(
            organization_id=organization_id,
            user_id=user_id,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            status=data.status,
        )
        self.db.add(contact)
        await self.db.flush()
        await self.audit.log(
            action="contact.created",
            entity_type="contact",
            entity_id=str(contact.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"email": contact.email, "status": contact.status},
        )
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update(self, organization_id: int, contact_id: int, data: ContactUpdate, user_id: int | None = None) -> Contact:
        contact = await self.get_by_id(organization_id, contact_id)
        if not contact:
            raise NotFoundError("Contact not found")

        update_data = data.model_dump(exclude_unset=True)
        if "email" in update_data and update_data["email"] != contact.email:
            existing = await self.get_by_email(organization_id, update_data["email"])
            if existing:
                raise ConflictError("Contact email already exists in this organization")

        for field, value in update_data.items():
            setattr(contact, field, value)

        await self.db.flush()
        await self.audit.log(
            action="contact.updated",
            entity_type="contact",
            entity_id=str(contact.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"updated_fields": sorted(update_data.keys())},
        )
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete(self, organization_id: int, contact_id: int, user_id: int | None = None) -> None:
        contact = await self.get_by_id(organization_id, contact_id)
        if not contact:
            raise NotFoundError("Contact not found")

        await self.audit.log(
            action="contact.deleted",
            entity_type="contact",
            entity_id=str(contact.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"email": contact.email},
        )
        await self.db.delete(contact)
        await self.db.flush()
        await self.db.commit()
