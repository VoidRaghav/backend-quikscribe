"""
Main API router that combines all module routes.
"""
from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.google_meeting_bot.routes import router as meeting_bot_router

# Create main API router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Include meeting bot routes
api_router.include_router(meeting_bot_router, prefix="/meeting-bot", tags=["Meeting Bot"])

