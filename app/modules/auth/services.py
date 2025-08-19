"""
Authentication services layer for business logic.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional

from app.modules.auth import repository
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, SocialAccountCreate

class AuthService:
    """Authentication service for handling business logic."""
    
    async def create_user(self, db: Session, user: UserCreate) -> User:
        """
        Create a new user with validation.
        
        Args:
            db: Database session
            user: User creation data
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If validation fails
        """
        # Check if email already exists
        if repository.get_user_by_email(db, user.email):
            raise ValueError("Email already registered")
        
        # Check if username already exists
        if repository.get_user_by_username(db, user.username):
            raise ValueError("Username already taken")
        
        return repository.create_user(db, user)
    
    async def authenticate_user(self, db: Session, email_or_username: str, password: str) -> Optional[User]:
        """
        Authenticate user with email/username and password.
        
        Args:
            db: Database session
            email_or_username: User email or username
            password: User password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        # Try to find user by email first
        user = repository.get_user_by_email(db, email_or_username)
        
        # If not found by email, try by username
        if not user:
            user = repository.get_user_by_username(db, email_or_username)
        
        # If still not found, return None
        if not user:
            return None
        
        # Verify password
        from app.core.security import verify_password
        if not verify_password(password, str(user.hashed_password)):
            return None
            
        return user
    
    async def get_or_create_social_user(self, db: Session, social_data: SocialAccountCreate) -> User:
        """
        Get or create user from social account data.
        
        Args:
            db: Database session
            social_data: Social account data
            
        Returns:
            User instance
        """
        return repository.get_or_create_social_user(db, social_data)
    
    async def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User instance if found, None otherwise
        """
        return repository.get_user_by_id(db, user_id)
    
    async def update_user_password(self, db: Session, user_id: str, new_password: str) -> User:
        """
        Update user password.
        
        Args:
            db: Database session
            user_id: User ID
            new_password: New password
            
        Returns:
            Updated user instance
            
        Raises:
            HTTPException: If user not found
        """
        user = repository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return repository.update_user_password(db, user, new_password)
    
    async def deactivate_user(self, db: Session, user_id: str) -> User:
        """
        Deactivate user account.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Updated user instance
            
        Raises:
            HTTPException: If user not found
        """
        user = repository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return repository.deactivate_user(db, user) 