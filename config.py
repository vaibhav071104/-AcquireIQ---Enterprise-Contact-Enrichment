"""
Configuration management for AcquireIQ
"""
import os
from typing import Optional


class Settings:
    """Application settings"""
    
    def __init__(self):
        # API Keys - pre-filled with your Hunter.io key
        self.hunter_api_key: Optional[str] = os.getenv(
            "HUNTER_API_KEY", 
            "00d17a35bfef2423200768ddecf7d27fc9dc9ca6"
        )
        
        # Database
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///acquireiq.db")
        
        # App Settings
        self.app_name: str = "AcquireIQ"
        self.app_version: str = "1.0.0"
        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"
        
        # Hunter.io API endpoints
        self.hunter_base_url: str = "https://api.hunter.io/v2"
        
        # Rate limiting
        self.max_requests_per_minute: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "50"))


# Global settings instance
settings = Settings()
