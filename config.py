"""
Configuration management for AcquireIQ
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    hunter_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///acquireiq.db"
    
    # App Settings
    app_name: str = "AcquireIQ"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Hunter.io API endpoints
    hunter_base_url: str = "https://api.hunter.io/v2"
    
    # Rate limiting
    max_requests_per_minute: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
