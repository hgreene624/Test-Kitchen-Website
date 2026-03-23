"""Dish model - menu item that candidates evaluate."""

from sqlalchemy import Column, String, Text, Boolean, DECIMAL, ForeignKey, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class Dish(Base, UUIDMixin, TimestampMixin):
    """Dish entity - menu item that candidates evaluate and provide feedback on."""

    __tablename__ = "dish"

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("menu_category.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dish_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    photo_urls = Column(ARRAY(Text), nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    category = relationship("MenuCategory", back_populates="dishes")
    feedback = relationship(
        "Feedback", back_populates="dish", cascade="all, delete-orphan"
    )
    proposals = relationship(
        "ProposedDish",
        back_populates="original_dish",
        foreign_keys="ProposedDish.original_dish_id",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_dish_category_id", "category_id"),
        Index("idx_dish_is_active", "is_active"),
        Index("idx_dish_name", "dish_name"),
    )
