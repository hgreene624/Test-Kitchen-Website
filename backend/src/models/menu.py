"""Menu model - restaurant menu for candidate review."""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class Menu(Base, UUIDMixin, TimestampMixin):
    """Menu entity - restaurant menu that candidates review."""

    __tablename__ = "menu"

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_by_admin_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    created_by_admin = relationship("AdminUser", back_populates="created_menus")
    categories = relationship(
        "MenuCategory", back_populates="menu", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_menu_is_active", "is_active"),
        Index("idx_menu_created_at", "created_at"),
    )
