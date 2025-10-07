"""
OAuth integration for social authentication.
"""
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi import HTTPException, status
import logging
from typing import Dict, Any, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize OAuth
oauth = OAuth()

# Track if Google OAuth is configured
google_oauth_configured = False

# Register OAuth providers
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    google_oauth_configured = True
    logger.info("Google OAuth provider registered successfully")
else:
    logger.warning("Google OAuth credentials not configured")

async def get_google_oauth_url(request: Request) -> RedirectResponse:
    """
    Generate Google OAuth authorization URL and redirect user.
    
    Args:
        request: FastAPI request object
        
    Returns:
        RedirectResponse to Google OAuth authorization URL
        
    Raises:
        RuntimeError: If Google OAuth is not configured
    """
    if not google_oauth_configured:
        raise RuntimeError("Google OAuth is not configured. Please check your environment variables.")
    
    # Additional check to ensure oauth.google exists
    if not hasattr(oauth, 'google') or oauth.google is None:
        raise RuntimeError("Google OAuth client is not properly initialized.")
    
    try:
        # Build absolute callback URL from your router
        redirect_uri = request.url_for("google_callback")
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error(f"Failed to generate Google OAuth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth flow"
        )

async def get_google_user_info(request: Request) -> Dict[str, Any]:
    """
    Exchange OAuth code for access token and get user information.
    
    Args:
        request: FastAPI request object containing OAuth callback data
        
    Returns:
        Dictionary containing user information from Google
        
    Raises:
        OAuthError: If token exchange fails
        HTTPException: If user info retrieval fails
    """
    if not google_oauth_configured:
        raise RuntimeError("Google OAuth is not configured. Please check your environment variables.")
    
    # Additional check to ensure oauth.google exists
    if not hasattr(oauth, 'google') or oauth.google is None:
        raise RuntimeError("Google OAuth client is not properly initialized.")
    
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)
        logger.debug("Successfully exchanged OAuth code for access token")
        
        # Get user info from token
        user_info = token.get("userinfo")
        if not user_info:
            # If userinfo not in token, parse from ID token
            user_info = await oauth.google.parse_id_token(request, token)
        
        # Validate required fields
        required_fields = ["sub", "email"]
        for field in required_fields:
            if field not in user_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field in OAuth response: {field}"
                )
        
        # Log successful authentication (without sensitive data)
        logger.info(f"Successfully retrieved user info for user: {user_info.get('email', 'unknown')}")
        
        return user_info
        
    except OAuthError as e:
        logger.error(f"OAuth error during token exchange: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during OAuth flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication process failed"
        )

# Future OAuth providers can be added here
async def get_facebook_oauth_url(request: Request) -> RedirectResponse:
    """
    Generate Facebook OAuth authorization URL (future implementation).
    
    Args:
        request: FastAPI request object
        
    Returns:
        RedirectResponse to Facebook OAuth authorization URL
    """
    # TODO: Implement Facebook OAuth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Facebook OAuth not yet implemented"
    )

async def get_github_oauth_url(request: Request) -> RedirectResponse:
    """
    Generate GitHub OAuth authorization URL (future implementation).
    
    Args:
        request: FastAPI request object
        
    Returns:
        RedirectResponse to GitHub OAuth authorization URL
    """
    # TODO: Implement GitHub OAuth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="GitHub OAuth not yet implemented"
    ) 