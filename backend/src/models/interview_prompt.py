"""InterviewPrompt model - video interview questions."""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class InterviewPrompt(Base, UUIDMixin, TimestampMixin):
    """InterviewPrompt entity - video interview question presented to candidates."""

    __tablename__ = "interview_prompt"

    prompt_text = Column(Text, nullable=False)
    sequence_order = Column(Integer, nullable=False, unique=True, index=True)
    time_limit_seconds = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_by_admin_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    created_by_admin = relationship("AdminUser", back_populates="created_prompts")
    video_recordings = relationship(
        "VideoRecording",
        back_populates="prompt",
        foreign_keys="VideoRecording.prompt_id",
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("time_limit_seconds IS NULL OR (time_limit_seconds >= 30 AND time_limit_seconds <= 300)", name="check_time_limit_range"),
        Index("idx_prompt_sequence_order", "sequence_order"),
        Index("idx_prompt_is_active", "is_active", "sequence_order"),
    )
