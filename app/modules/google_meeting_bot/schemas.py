"""
Pydantic schemas for Google Meeting Bot API
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class MeetingStartRequest(BaseModel):
    """Request schema for starting a meeting bot."""
    meeting_url: HttpUrl
    duration: Optional[int] = 60

class MeetingResponse(BaseModel):
    """Response schema for meeting bot operations."""
    message: str
    meeting_id: str
    container_id: Optional[str] = None
    port: Optional[int] = None
    status: Optional[str] = None

class MeetingStatusResponse(BaseModel):
    """Response schema for meeting status."""
    id: str
    user_id: str
    meeting_id: str
    meeting_url: str
    meeting_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    container_id: Optional[str] = None
    port: Optional[int] = None
    status: str
    bot_logs: Optional[str] = None
    meeting_created_at: datetime
    meeting_started_at: Optional[datetime] = None
    meeting_ended_at: Optional[datetime] = None
    meeting_updated_at: datetime

    class Config:
        from_attributes = True

class MeetingControlRequest(BaseModel):
    """Request schema for meeting control operations."""
    action: str  # "pause", "resume", "stop"

class MeetingControlResponse(BaseModel):
    """Response schema for meeting control operations."""
    message: str
    meeting_id: str
    action: str
    success: bool
    timestamp: datetime = datetime.now()

class PortUsageStats(BaseModel):
    """Schema for port usage statistics."""
    total_ports_available: int
    ports_in_use: int
    ports_available: int
    active_containers: int
    port_range: tuple[int, int]

class MeetingBotStatus(BaseModel):
    """Schema for meeting bot status."""
    container_id: str
    container_name: str
    port: int
    meeting_uuid: str
    user_id: str
    meeting_url: str
    status: str
    docker_status: str
    running: bool
    started_at: float

