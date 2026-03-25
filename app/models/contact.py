import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.organization import Organization
    from app.models.user import User


class ContactStatus(str, enum.Enum):
    ACTIVE      = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED     = "bounced"
    COMPLAINED  = "complained"


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    # ── Identity ──────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship("Organization", back_populates="contacts")
    user: Mapped["User"] = relationship("User", back_populates="contacts")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="contact", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email

    def __repr__(self) -> str:
        return f"<Contact id={self.id} email={self.email!r} status={self.status}>"
