from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.contact import Contact
    from app.models.membership import Membership
    from app.models.payment import Payment
    from app.models.user import User


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    owner: Mapped["User"] = relationship("User", back_populates="organizations_owned")
    memberships: Mapped[List["Membership"]] = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="organization", cascade="all, delete-orphan")
    campaigns: Mapped[List["Campaign"]] = relationship("Campaign", back_populates="organization", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug!r}>"
