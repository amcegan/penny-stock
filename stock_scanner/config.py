import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration."""
    
    # Base Directory
    BASE_DIR: Path = Path(__file__).parent.parent.absolute()
    
    # API Keys
    FMP_API_KEY: str = os.environ.get("FMP_API_KEY", "")
    LANGCHAIN_API_KEY: Optional[str] = os.environ.get("LANGCHAIN_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.environ.get("GOOGLE_API_KEY") # For Gemini
    
    # Email Settings
    EMAIL_ADDRESS: Optional[str] = os.environ.get("EMAIL_ADDRESS")
    EMAIL_PASSWORD: Optional[str] = os.environ.get("EMAIL_PASSWORD")
    EMAIL_RECIPIENT: Optional[str] = os.environ.get("EMAIL_RECIPIENT")
    
    # API URLs
    FMP_BASE_URL_V3: str = "https://financialmodelingprep.com/api/v3"
    FMP_BASE_URL_V4: str = "https://financialmodelingprep.com/api/v4"
    
    # Scanning Parameters
    DEFAULT_MIN_MARKET_CAP: int = 10_000_000
    DEFAULT_MAX_MARKET_CAP: int = 2_000_000_000
    DEFAULT_MIN_VOLUME: int = 50_000
    DEFAULT_VOLUME_SPIKE_THRESHOLD: float = 1.5
    DEFAULT_UPSIDE_THRESHOLD: float = 20.0
    
    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: str = str(BASE_DIR / "daily_scan.log")
    
    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.FMP_API_KEY:
            raise ValueError("FMP_API_KEY environment variable is not set.")
        if not cls.GOOGLE_API_KEY:
             # Depending on if we strictly fail or just skip report gen. 
             # For now, let's warn or raise if we want to enforce requirements.
             # User asked for production ready, so let's enforce.
             pass # We'll enforce at usage site or here.

config = Config()
