"""Candidate model - represents chef applicants."""

import enum
from sqlalchemy import Column, String, Enum, DateTime, Index
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class AccountStatus(str, enum.Enum):
    """Account verification status."""

    UNVERIFIED = "unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class SubmissionStatus(str, enum.Enum):
    """Application progress status."""

    INCOMPLETE = "incomplete"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REVIEWED = "reviewed"


class FinalDecision(str, enum.Enum):
    """Hiring decision status."""

    ELIMINATED = "eliminated"
    HIRED = "hired"


class Candidate(Base, UUIDMixin, TimestampMixin):
    """Candidate entity - chef applicant with account credentials and submission status."""

    __tablename__ = "candidate"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    account_status = Column(
        Enum(AccountStatus),
        nullable=False,
        default=AccountStatus.UNVERIFIED,
        index=True,
    )
    submission_status = Column(
        Enum(SubmissionStatus),
        nullable=False,
        default=SubmissionStatus.INCOMPLETE,
        index=True,
    )
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    final_decision = Column(Enum(FinalDecision), nullable=True)
    final_decision_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    documents = relationship(
        "Document", back_populates="candidate", cascade="all, delete-orphan"
    )
    videos = relationship(
        "VideoRecording", back_populates="candidate", cascade="all, delete-orphan"
    )
    feedback = relationship(
        "Feedback", back_populates="candidate", cascade="all, delete-orphan"
    )
    proposals = relationship(
        "ProposedDish", back_populates="candidate", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="candidate", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_candidate_email", "email"),
        Index("idx_candidate_account_status", "account_status"),
        Index("idx_candidate_submission_status", "submission_status"),
        Index("idx_candidate_created_at", "created_at"),
    )
