"""AuditLog model - records all admin actions for compliance."""

import enum
from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class ActionType(str, enum.Enum):
    """Admin action types for audit logging."""

    VIEW_CANDIDATE_LIST = "VIEW_CANDIDATE_LIST"
    VIEW_CANDIDATE_DETAIL = "VIEW_CANDIDATE_DETAIL"
    DOWNLOAD_DOCUMENT = "DOWNLOAD_DOCUMENT"
    DOWNLOAD_TRANSCRIPT = "DOWNLOAD_TRANSCRIPT"
    VIEW_VIDEO = "VIEW_VIDEO"
    UPDATE_CANDIDATE_STATUS = "UPDATE_CANDIDATE_STATUS"
    SET_FINAL_DECISION = "SET_FINAL_DECISION"
    CREATE_INTERVIEW_PROMPT = "CREATE_INTERVIEW_PROMPT"
    UPDATE_INTERVIEW_PROMPT = "UPDATE_INTERVIEW_PROMPT"
    DELETE_INTERVIEW_PROMPT = "DELETE_INTERVIEW_PROMPT"
    CREATE_MENU = "CREATE_MENU"
    UPDATE_MENU = "UPDATE_MENU"
    DELETE_MENU = "DELETE_MENU"


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """AuditLog entity - records all admin actions for security and compliance."""

    __tablename__ = "audit_log"

    admin_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admin_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type = Column(String(100), nullable=False, index=True)
    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    action_metadata = Column(JSONB, nullable=True)

    # Relationships
    admin_user = relationship("AdminUser", back_populates="audit_logs")
    candidate = relationship("Candidate", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("idx_audit_admin_id", "admin_user_id", "created_at"),
        Index("idx_audit_candidate_id", "candidate_id", "created_at"),
        Index("idx_audit_action_type", "action_type", "created_at"),
        Index("idx_audit_created_at", "created_at"),
    )
