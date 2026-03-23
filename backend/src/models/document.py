"""Document model - uploaded resume and cover letter files."""

import enum
from sqlalchemy import Column, String, Integer, Text, Enum, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class DocumentType(str, enum.Enum):
    """Type of document uploaded by candidate."""

    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class Document(Base, UUIDMixin, TimestampMixin):
    """Document entity - candidate's uploaded resume or cover letter."""

    __tablename__ = "document"

    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type = Column(Enum(DocumentType), nullable=False)
    file_url = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(Text, nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="documents")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("file_size_bytes <= 10485760", name="check_file_size_max_10mb"),
        UniqueConstraint("candidate_id", "document_type", name="unique_candidate_document_type"),
        Index("idx_document_candidate_id", "candidate_id"),
        Index("idx_document_type", "candidate_id", "document_type"),
    )
