import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class PaymentStatus(str, enum.Enum):
    PENDING   = "pending"
    SUCCEEDED = "succeeded"
    FAILED    = "failed"
    REFUNDED  = "refunded"
    DISPUTED  = "disputed"


class PaymentProvider(str, enum.Enum):
    STRIPE  = "stripe"
    PAYPAL  = "paypal"
    MPESA   = "mpesa"
    MANUAL  = "manual"


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    # ── Identity ──────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Amount ────────────────────────────────────────────────────────────────
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="STRIPE", nullable=False)
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    provider_metadata: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship("Organization", back_populates="payments")
    user: Mapped["User"] = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} amount={self.amount} {self.currency} status={self.status}>"
