import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.contact import Contact


class MessageStatus(str, enum.Enum):
    PENDING   = "pending"
    QUEUED    = "queued"
    SENT      = "sent"
    DELIVERED = "delivered"
    OPENED    = "opened"
    CLICKED   = "clicked"
    BOUNCED   = "bounced"
    FAILED    = "failed"


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    # ── Identity ──────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Content ───────────────────────────────────────────────────────────────
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)

    # ── Tracking timestamps ───────────────────────────────────────────────────
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    bounced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Error tracking ────────────────────────────────────────────────────────
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="messages")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} status={self.status} contact_id={self.contact_id}>"
