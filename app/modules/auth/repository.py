"""
Authentication repository layer for data access operations.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from typing import Optional

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, oauth2_scheme, verify_token
from app.modules.auth.models import User, SocialAccount
from app.modules.auth.schemas import UserCreate, SocialAccountCreate

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user account.
    
    Args:
        db: Database session
        user: User creation data
        
    Returns:
        Created user instance
        
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User instance if authentication successful, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):  # Convert to str
        return None
    return user

def get_social_account(db: Session, provider: str, provider_user_id: str) -> Optional[SocialAccount]:
    """Get social account by provider and provider user ID."""
    return db.query(SocialAccount).filter(
        SocialAccount.provider == provider,
        SocialAccount.provider_user_id == provider_user_id
    ).first()

def create_social_account(db: Session, social_account: SocialAccountCreate, user_id: str) -> SocialAccount:
    """Create a new social account linked to a user."""
    db_social_account = SocialAccount(
        provider=social_account.provider,
        provider_user_id=social_account.provider_user_id,
        email=social_account.email,
        user_id=user_id
    )
    db.add(db_social_account)
    db.commit()
    db.refresh(db_social_account)
    return db_social_account

def get_or_create_social_user(db: Session, social_data: SocialAccountCreate) -> User:
    """
    Get existing user or create new user from social account data.
    
    Args:
        db: Database session
        social_data: Social account creation data
        
    Returns:
        User instance (existing or newly created)
    """
    # Check if social account exists
    social_account = get_social_account(db, social_data.provider, social_data.provider_user_id)
    
    if social_account:
        # Return existing user
        return social_account.user
    
    # Check if user with this email exists
    user = get_user_by_email(db, social_data.email)
    
    if not user:
        # Create new user with random password
        import secrets
        random_password = secrets.token_urlsafe(16)
        username = social_data.email.split('@')[0]
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while get_user_by_username(db, username):
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            email=social_data.email,
            username=username,
            hashed_password=get_password_hash(random_password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create social account linked to user
    create_social_account(db, social_data, str(user.id))  # Convert to str
    
    return user

def update_user_password(db: Session, user: User, new_password: str) -> User:
    """Update user password."""
    setattr(user, 'hashed_password', get_password_hash(new_password))  # Use setattr
    db.commit()
    db.refresh(user)
    return user

def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    """
    Change user password with current password verification.
    
    Args:
        db: Database session
        user: User instance
        current_password: Current password for verification
        new_password: New password to set
        
    Returns:
        Updated user instance
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(current_password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    return update_user_password(db, user, new_password)

def generate_password_reset_token(email: str) -> str:
    """
    Generate password reset token.
    
    Args:
        email: User email
        
    Returns:
        Password reset token
    """
    from app.core.security import create_access_token
    from datetime import timedelta
    
    # Create token that expires in 30 minutes
    token_data = {"sub": email, "type": "password_reset"}
    token = create_access_token(
        data=token_data, 
        expires_delta=timedelta(minutes=30)
    )
    return token

def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return email.
    
    Args:
        token: Password reset token
        
    Returns:
        Email if token is valid, None otherwise
    """
    payload = verify_token(token)
    if not payload:
        return None
    
    # Check if it's a password reset token
    if payload.get("type") != "password_reset":
        return None
    
    email = payload.get("sub")
    return email if email else None

def reset_password_with_token(db: Session, token: str, new_password: str) -> User:
    """
    Reset password using reset token.
    
    Args:
        db: Database session
        token: Password reset token
        new_password: New password
        
    Returns:
        Updated user instance
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token and get email
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user by email
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    return update_user_password(db, user, new_password)

def deactivate_user(db: Session, user: User) -> User:
    """Deactivate user account."""
    setattr(user, 'is_active', False)  # Use setattr
    db.commit()
    db.refresh(user)
    return user

# FastAPI Dependencies
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Get current user from JWT token.
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        Current user instance
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify and decode token
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
    
    user_id = payload.get("sub")  # Remove type annotation
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = get_user_by_id(db, str(user_id))  # Convert to str
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user instance
        
    Raises:
        HTTPException: If user is inactive
    """
    if not bool(current_user.is_active):  # Convert to bool explicitly
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user 