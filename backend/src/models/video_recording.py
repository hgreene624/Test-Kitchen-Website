"""VideoRecording model - candidate video interview responses."""

import enum
from sqlalchemy import Column, String, Text, Integer, BigInteger, Enum, DateTime, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class TranscriptionStatus(str, enum.Enum):
    """Transcription processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class VideoRecording(Base, UUIDMixin, TimestampMixin):
    """VideoRecording entity - candidate's video response to interview prompt."""

    __tablename__ = "video_recording"

    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interview_prompt.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    file_url = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(Text, nullable=False)
    transcription_status = Column(
        Enum(TranscriptionStatus),
        nullable=False,
        default=TranscriptionStatus.PENDING,
        index=True,
    )
    transcription_started_at = Column(DateTime(timezone=True), nullable=True)
    transcription_completed_at = Column(DateTime(timezone=True), nullable=True)
    transcription_error = Column(Text, nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="videos")
    prompt = relationship("InterviewPrompt", back_populates="video_recordings")
    transcript = relationship(
        "Transcript",
        back_populates="video_recording",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("duration_seconds <= 300", name="check_duration_max_5min"),
        UniqueConstraint("candidate_id", "prompt_id", name="unique_candidate_prompt_response"),
        Index("idx_video_candidate_id", "candidate_id"),
        Index("idx_video_transcription_status", "transcription_status", "created_at"),
        Index("idx_video_candidate_prompt", "candidate_id", "prompt_id"),
    )
