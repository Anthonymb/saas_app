from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.audit import AuditService


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit = AuditService(db)

    async def list_by_organization(
        self,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        provider: str | None = None,
        provider_ref: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Payment], int]:
        offset = (page - 1) * page_size
        filters = [Payment.organization_id == organization_id]
        if status:
            filters.append(Payment.status == status)
        if provider:
            filters.append(Payment.provider == provider)
        if provider_ref:
            filters.append(Payment.provider_ref.ilike(f"%{provider_ref}%"))
        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Payment.provider.ilike(term),
                    Payment.provider_ref.ilike(term),
                    Payment.currency.ilike(term),
                )
            )

        total_result = await self.db.execute(
            select(func.count(Payment.id)).where(*filters)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Payment)
            .where(*filters)
            .order_by(Payment.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, organization_id: int, payment_id: int) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(
                Payment.organization_id == organization_id,
                Payment.id == payment_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider_ref(self, organization_id: int, provider_ref: str) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(
                Payment.organization_id == organization_id,
                Payment.provider_ref == provider_ref,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, organization_id: int, user_id: int, data: PaymentCreate) -> Payment:
        if data.provider_ref:
            existing = await self.get_by_provider_ref(organization_id, data.provider_ref)
            if existing:
                raise ConflictError("Payment provider reference already exists in this organization")

        payment = Payment(
            organization_id=organization_id,
            user_id=user_id,
            amount=data.amount,
            currency=data.currency,
            status=data.status,
            provider=data.provider,
            provider_ref=data.provider_ref,
            provider_metadata=data.provider_metadata,
            paid_at=data.paid_at,
            refunded_at=data.refunded_at,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.audit.log(
            action="payment.created",
            entity_type="payment",
            entity_id=str(payment.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={
                "amount": float(payment.amount),
                "currency": payment.currency,
                "provider": payment.provider,
                "status": payment.status,
            },
        )
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def update(
        self,
        organization_id: int,
        payment_id: int,
        data: PaymentUpdate,
        user_id: int | None = None,
    ) -> Payment:
        payment = await self.get_by_id(organization_id, payment_id)
        if not payment:
            raise NotFoundError("Payment not found")

        update_data = data.model_dump(exclude_unset=True)
        if "provider_ref" in update_data and update_data["provider_ref"] != payment.provider_ref and update_data["provider_ref"]:
            existing = await self.get_by_provider_ref(organization_id, update_data["provider_ref"])
            if existing:
                raise ConflictError("Payment provider reference already exists in this organization")

        for field, value in update_data.items():
            setattr(payment, field, value)

        await self.db.flush()
        await self.audit.log(
            action="payment.updated",
            entity_type="payment",
            entity_id=str(payment.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"updated_fields": sorted(update_data.keys())},
        )
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def delete(self, organization_id: int, payment_id: int, user_id: int | None = None) -> None:
        payment = await self.get_by_id(organization_id, payment_id)
        if not payment:
            raise NotFoundError("Payment not found")

        await self.audit.log(
            action="payment.deleted",
            entity_type="payment",
            entity_id=str(payment.id),
            organization_id=organization_id,
            user_id=user_id,
            metadata={"provider_ref": payment.provider_ref, "status": payment.status},
        )
        await self.db.delete(payment)
        await self.db.flush()
        await self.db.commit()
