"""Feedback model - candidate evaluation of a dish."""

from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class Feedback(Base, UUIDMixin, TimestampMixin):
    """Feedback entity - candidate's evaluation of a dish."""

    __tablename__ = "feedback"

    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dish_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dish.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating = Column(Integer, nullable=True)  # NULL allowed for partial feedback
    comment_text = Column(Text, nullable=True)  # NULL allowed for partial feedback
    should_eliminate = Column(Boolean, nullable=False, default=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="feedback")
    dish = relationship("Dish", back_populates="feedback")
    proposals = relationship(
        "ProposedDish", back_populates="feedback", cascade="all, delete-orphan"
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="check_rating_range"),
        CheckConstraint("comment_text IS NULL OR length(comment_text) <= 500", name="check_comment_length"),
        UniqueConstraint("candidate_id", "dish_id", name="unique_candidate_dish_feedback"),
        Index("idx_feedback_candidate_id", "candidate_id"),
        Index("idx_feedback_dish_id", "dish_id"),
        Index("idx_feedback_rating", "dish_id", "rating"),
        Index("idx_feedback_candidate_dish", "candidate_id", "dish_id"),
    )
