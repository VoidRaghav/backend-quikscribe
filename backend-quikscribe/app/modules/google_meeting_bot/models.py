"""
Google Meeting Bot Models
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text
import uuid
from datetime import datetime, timezone
from app.core.database import Base



class User_google_meeting_data(Base):
    __tablename__ = "user_google_meeting_data"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    meeting_id = Column(String, nullable=False, index=True)
    meeting_url = Column(String, nullable=False)  # Store full URL
    meeting_duration = Column(Integer, nullable=True)  # Expected duration
    actual_duration = Column(Integer, nullable=True)  # Actual duration when meeting ends
    container_id = Column(String, nullable=True)  # Docker container ID
    port = Column(Integer, nullable=True)  # Port used
    status = Column(String, default="active", nullable=False)  # active, ended, failed
    bot_logs = Column(Text, nullable=True)  # Store bot logs/transcription
    meeting_created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    meeting_started_at = Column(DateTime, nullable=True)  # When bot actually joined
    meeting_ended_at = Column(DateTime, nullable=True)  # When meeting actually ended
    meeting_updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

