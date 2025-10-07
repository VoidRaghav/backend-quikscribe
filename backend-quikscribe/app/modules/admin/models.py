"""
Admin module database models.
"""
from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.core.database import Base

class AdminUser(Base):
    """Admin user model for storing admin account information."""
    
    __tablename__ = "admin_users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # Link to regular user
    role = Column(String, nullable=False, default="admin")  # admin, super_admin, moderator
    permissions = Column(Text)  # JSON string of permissions
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class SystemSetting(Base):
    """System settings model."""
    
    __tablename__ = "system_settings"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    created_by = Column(String, ForeignKey("admin_users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    admin = relationship("AdminUser", foreign_keys=[created_by])

class AuditLog(Base):
    """Audit log for tracking admin actions."""
    
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    admin_user_id = Column(String, ForeignKey("admin_users.id"), nullable=False)
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, etc.
    resource_type = Column(String, nullable=False)  # user, setting, etc.
    resource_id = Column(String)  # ID of the affected resource
    details = Column(Text)  # JSON string with additional details
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    admin = relationship("AdminUser", foreign_keys=[admin_user_id]) 