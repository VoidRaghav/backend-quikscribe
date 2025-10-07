"""
QuikScribe Backend API - Main Application Entry Point
"""
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import get_settings
from app.core.database import init_db
from app.api.route import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting QuikScribe API server...")
    logger.info(f"Environment: {'DEBUG' if settings.debug else 'PRODUCTION'}")
    init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down QuikScribe API server...")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="API for QuikScribe application with modular architecture",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
    contact={
        "name": "QuikScribe Team",
        "url": "https://quikscribe.com",
        "email": "support@quikscribe.com"
    },
    license_info={
        "name": "QuikScribe License",
        "url": "https://quikscribe.com/license"
    }
)

def custom_openapi():
    """Custom OpenAPI schema with correct security scheme."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Fix the OAuth2 security scheme
    if "components" in openapi_schema and "securitySchemes" in openapi_schema["components"]:
        if "OAuth2PasswordBearer" in openapi_schema["components"]["securitySchemes"]:
            openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"] = "/api/v1/auth/token"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Add session middleware for OAuth
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.secret_key,
    max_age=settings.access_token_expire_minutes * 60
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to QuikScribe API",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else "Contact support for API documentation",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": "2024-01-01T00:00:00Z"  # You can use datetime.utcnow()
    }

# Include API router with all module routes
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )