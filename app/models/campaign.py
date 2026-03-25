import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.organization import Organization
    from app.models.user import User


class CampaignStatus(str, enum.Enum):
    DRAFT     = "draft"
    SCHEDULED = "scheduled"
    SENDING   = "sending"
    SENT      = "sent"
    PAUSED    = "paused"
    CANCELLED = "cancelled"


class CampaignChannel(str, enum.Enum):
    EMAIL = "email"
    SMS   = "sms"
    PUSH  = "push"


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"

    # ── Identity ──────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Status & channel ──────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), default="EMAIL", nullable=False)
    # ── Timestamps ────────────────────────────────────────────────────────────
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship("Organization", back_populates="campaigns")
    user: Mapped["User"] = relationship("User", back_populates="campaigns")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="campaign", cascade="all, delete-orphan")

    @property
    def total_sent(self) -> int:
        return len([m for m in self.messages if m.status == "sent"])

    @property
    def total_opened(self) -> int:
        return len([m for m in self.messages if m.opened_at is not None])

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} name={self.name!r} status={self.status}>"
