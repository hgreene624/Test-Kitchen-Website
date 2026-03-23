"""Transcript model - transcribed text from video recordings."""

from sqlalchemy import Column, String, Text, Integer, DECIMAL, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class Transcript(Base, UUIDMixin, TimestampMixin):
    """Transcript entity - transcribed text content from video recording."""

    __tablename__ = "transcript"

    video_recording_id = Column(
        UUID(as_uuid=True),
        ForeignKey("video_recording.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    transcript_text = Column(Text, nullable=False)
    confidence_score = Column(DECIMAL(3, 2), nullable=False)
    word_count = Column(Integer, nullable=False)
    file_url = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(Text, nullable=False)
    provider = Column(String(50), nullable=False, default="assemblyai")
    provider_metadata = Column(JSONB, nullable=True)

    # Relationships
    video_recording = relationship("VideoRecording", back_populates="transcript")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="check_confidence_score_range"),
        Index("idx_transcript_video_recording_id", "video_recording_id"),
        Index("idx_transcript_confidence_score", "confidence_score"),
    )
