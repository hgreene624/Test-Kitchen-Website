"""ProposedDish model - candidate's alternative dish proposals."""

from sqlalchemy import Column, Text, ForeignKey, Index, CheckConstraint, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class ProposedDish(Base, UUIDMixin, TimestampMixin):
    """ProposedDish entity - candidate's alternative dish proposal with photos."""

    __tablename__ = "proposed_dish"

    feedback_id = Column(
        UUID(as_uuid=True),
        ForeignKey("feedback.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_dish_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dish.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposal_description = Column(Text, nullable=True)
    photo_urls = Column(ARRAY(Text), nullable=False)

    # Relationships
    feedback = relationship("Feedback", back_populates="proposals")
    candidate = relationship("Candidate", back_populates="proposals")
    original_dish = relationship("Dish", back_populates="proposals")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("array_length(photo_urls, 1) <= 5 AND array_length(photo_urls, 1) >= 1", name="check_photo_urls_count"),
        Index("idx_proposal_feedback_id", "feedback_id"),
        Index("idx_proposal_candidate_id", "candidate_id"),
        Index("idx_proposal_dish_id", "original_dish_id"),
    )
