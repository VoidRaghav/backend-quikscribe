"""
Authentication routes for user registration, login, and OAuth.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, verify_token
from app.modules.auth import repository
from app.modules.auth.schemas import (
    UserCreate, UserResponse, Token, SocialAccountCreate, PasswordChange,
    PasswordReset, PasswordResetConfirm
)
from app.modules.auth.oauth import get_google_oauth_url, get_google_user_info
from app.modules.auth.services import AuthService
from app.modules.auth.models import User

# Initialize router and logger
auth_router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

@auth_router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate, 
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends()
):
    """Register a new user with email, username and password."""
    try:
        return await auth_service.create_user(db, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends()
):
    """Login with username/email and password to get access token."""
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

@auth_router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(repository.get_current_active_user)
):
    """Get current user information."""
    return current_user

@auth_router.get("/google/login", name="google_login")
async def google_login(request: Request):
    """Redirect user to Google for authentication."""
    try:
        return await get_google_oauth_url(request)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@auth_router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request, 
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends()
):
    """Handle Google's response, create/join user, then redirect to frontend."""
    try:
        user_info = await get_google_user_info(request)
    except Exception as e:
        logger.error("Google OAuth Error", exc_info=True)
        return RedirectResponse(f"{settings.frontend_url}/oauth-error?error={str(e)}")

    # Create social account data
    social = SocialAccountCreate(
        provider="google",
        provider_user_id=user_info["sub"],
        email=user_info["email"],
    )
    
    try:
        user = await auth_service.get_or_create_social_user(db, social)
        
        access_expires = timedelta(minutes=settings.access_token_expire_minutes)
        token = create_access_token(
            data={"sub": user.id}, 
            expires_delta=access_expires
        )

        # Redirect back to frontend with token
        return RedirectResponse(f"{settings.frontend_url}/oauth-success?token={token}")
        
    except Exception as e:
        logger.error("Error creating/finding social user", exc_info=True)
        return RedirectResponse(f"{settings.frontend_url}/oauth-error?error=account_creation_failed")

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(repository.get_current_user)
):
    """Refresh access token."""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.id}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

@auth_router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(repository.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        repository.change_password(
            db=db,
            user=current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions from repository
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset token."""
    try:
        # Check if user exists
        user = repository.get_user_by_email(db, password_reset.email)
        if not user:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token
        reset_token = repository.generate_password_reset_token(password_reset.email)
        
        # TODO: Send email with reset token
        # For now, we'll just log it (in production, you'd send an email)
        logger.info(f"Password reset token for {password_reset.email}: {reset_token}")
        
        return {
            "message": "If the email exists, a reset link has been sent",
            "reset_token": reset_token  # Remove this in production!
        }
        
    except Exception as e:
        logger.error(f"Error in forgot password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password with token."""
    try:
        repository.reset_password_with_token(
            db=db,
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        # Re-raise HTTP exceptions from repository
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 