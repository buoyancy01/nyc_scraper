"""
Configuration management for NYC Violations system
"""

import os
from typing import List, Optional


class Settings:
    """Application settings from environment variables"""
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # NYC Open Data API
    NYC_API_BASE_URL: str = os.getenv(
        "NYC_API_BASE_URL", 
        "https://data.cityofnewyork.us/resource/nc67-uf89.json"
    )
    NYC_API_TIMEOUT: int = int(os.getenv("NYC_API_TIMEOUT", "30"))
    
    # 2Captcha settings
    TWOCAPTCHA_API_KEY: Optional[str] = os.getenv("CAPTCHA_API_KEY")  # Changed from TWOCAPTCHA_API_KEY
    CAPTCHA_TIMEOUT: int = int(os.getenv("CAPTCHA_TIMEOUT", "300"))
    
    # Proxy settings
    PROXY_LIST: Optional[str] = os.getenv("PROXY_LIST")
    
    @property
    def proxies(self) -> List[str]:
        """Parse proxy list from environment variable"""
        if not self.PROXY_LIST:
            return []
        return [proxy.strip() for proxy in self.PROXY_LIST.split(",") if proxy.strip()]
    
    # Web scraping settings
    SCRAPING_DELAY: float = float(os.getenv("SCRAPING_DELAY", "2.0"))
    MAX_SCRAPE_VIOLATIONS: int = int(os.getenv("MAX_SCRAPE_VIOLATIONS", "50"))
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))
    
    # File storage
    DOWNLOADS_DIR: str = os.getenv("DOWNLOADS_DIR", "./downloads")
    PDF_DIR: str = os.getenv("PDF_DIR", "./downloads/pdfs")
    
    # Database settings (optional)
    MONGODB_URL: Optional[str] = os.getenv("MONGODB_URL")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "nyc_violations")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate limiting
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))  # requests per minute
    
    # Security
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    def __init__(self):
        """Initialize settings and create directories"""
        os.makedirs(self.DOWNLOADS_DIR, exist_ok=True)
        os.makedirs(self.PDF_DIR, exist_ok=True)
    
    @property
    def has_captcha_key(self) -> bool:
        """Check if 2Captcha API key is configured"""
        return bool(self.TWOCAPTCHA_API_KEY and self.TWOCAPTCHA_API_KEY.strip())
    
    @property
    def has_proxies(self) -> bool:
        """Check if proxies are configured"""
        return len(self.proxies) > 0
    
    @property
    def has_database(self) -> bool:
        """Check if database is configured"""
        return bool(self.MONGODB_URL)


# Global settings instance
settings = Settings()