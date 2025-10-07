"""
Application configuration settings.
"""
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # App Info
    app_name: str = "QuikScribe Backend API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    
    # Frontend
    frontend_allowed_origins: str = Field(validation_alias="FRONTEND_ALLOWED_ORIGINS")
    frontend_url: str = Field(validation_alias="FRONTEND_URL")
    
    # Authentication
    secret_key: str = Field(validation_alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # OAuth
    google_client_id: str = Field(default="", validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", validation_alias="GOOGLE_CLIENT_SECRET")
    
    # Database
    db_host: str = Field(validation_alias="DB_HOST")
    db_port: int = Field(validation_alias="DB_PORT")
    db_user: str = Field(validation_alias="DB_USER")
    db_password: str = Field(validation_alias="DB_PASSWORD")
    db_name: str = Field(validation_alias="DB_NAME")
    
    # Docker Image for Google Meeting Bot
    docker_image_name: str = Field(validation_alias="DOCKER_IMAGE_NAME")
    
    @property
    def database_url(self) -> str:
        """Get database URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def allowed_origins(self) -> List[str]:
        """Get list of allowed origins."""
        return [origin.strip() for origin in self.frontend_allowed_origins.split(",")]

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg] 