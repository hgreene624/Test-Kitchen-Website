"""AdminUser model - staff admin who reviews candidates."""

from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class AdminUser(Base, UUIDMixin, TimestampMixin):
    """AdminUser entity - staff admin with review and management permissions."""

    __tablename__ = "admin_user"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    created_prompts = relationship(
        "InterviewPrompt",
        back_populates="created_by_admin",
        foreign_keys="InterviewPrompt.created_by_admin_id",
    )
    created_menus = relationship(
        "Menu",
        back_populates="created_by_admin",
        foreign_keys="Menu.created_by_admin_id",
    )
    audit_logs = relationship("AuditLog", back_populates="admin_user")

    # Indexes
    __table_args__ = (
        Index("idx_admin_email", "email"),
        Index("idx_admin_is_active", "is_active"),
    )
