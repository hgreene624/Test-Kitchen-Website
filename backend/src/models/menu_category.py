"""MenuCategory model - menu section (appetizers, mains, etc.)."""

from sqlalchemy import Column, String, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class MenuCategory(Base, UUIDMixin, TimestampMixin):
    """MenuCategory entity - section of a menu (e.g., Appetizers, Entrees)."""

    __tablename__ = "menu_category"

    menu_id = Column(
        UUID(as_uuid=True),
        ForeignKey("menu.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_name = Column(String(100), nullable=False)
    sequence_order = Column(Integer, nullable=False, index=True)

    # Relationships
    menu = relationship("Menu", back_populates="categories")
    dishes = relationship(
        "Dish", back_populates="category", cascade="all, delete-orphan"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("menu_id", "sequence_order", name="unique_menu_category_order"),
        UniqueConstraint("menu_id", "category_name", name="unique_menu_category_name"),
        Index("idx_category_menu_id", "menu_id", "sequence_order"),
        Index("idx_category_sequence_order", "menu_id", "sequence_order"),
    )
