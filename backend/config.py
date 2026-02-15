"""
Configuration settings for Bank Statement Extractor.
Centralized configuration management for the application.
"""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Application configuration class."""
    
    # Application Settings
    APP_NAME = "Bank Statement Transaction Extractor"
    VERSION = "2.0.0"
    
    # File Upload Settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_FILE_TYPES: list[str] = [".pdf"]
    
    # Output Settings
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output"))
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "./logs"))
    
    # Validation Settings
    STRICT_MODE: bool = os.getenv("STRICT_MODE", "false").lower() == "true"
    ALLOW_ZERO_AMOUNTS: bool = os.getenv("ALLOW_ZERO_AMOUNTS", "false").lower() == "true"
    MAX_TRANSACTION_AMOUNT: float = float(os.getenv("MAX_TRANSACTION_AMOUNT", "1000000.00"))
    MIN_DESCRIPTION_LENGTH: int = int(os.getenv("MIN_DESCRIPTION_LENGTH", "3"))
    
    # Processing Settings
    MAX_CONTINUATION_LINES: int = int(os.getenv("MAX_CONTINUATION_LINES", "10"))
    BALANCE_THRESHOLD: float = float(os.getenv("BALANCE_THRESHOLD", "100000.00"))
    ENABLE_OCR_FALLBACK: bool = os.getenv("ENABLE_OCR_FALLBACK", "false").lower() == "true"
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # API Settings (for future use)
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Frontend Settings
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "0.0.0.0")
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8501"))
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_output_path(cls, filename: str) -> Path:
        """Get full path for output file."""
        cls.ensure_directories()
        return cls.OUTPUT_DIR / filename
    
    @classmethod
    def get_log_path(cls, filename: str) -> Path:
        """Get full path for log file."""
        cls.ensure_directories()
        return cls.LOG_DIR / filename
    
    @classmethod
    def validate_file(cls, filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check file type
        if not any(filename.lower().endswith(ext) for ext in cls.ALLOWED_FILE_TYPES):
            return False, f"Invalid file type. Allowed types: {', '.join(cls.ALLOWED_FILE_TYPES)}"
        
        # Check file size
        if file_size > cls.MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large ({size_mb:.2f} MB). Maximum: {cls.MAX_FILE_SIZE_MB} MB"
        
        # Check if empty
        if file_size == 0:
            return False, "File is empty"
        
        return True, None
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert configuration to dictionary."""
        return {
            "app_name": cls.APP_NAME,
            "version": cls.VERSION,
            "max_file_size_mb": cls.MAX_FILE_SIZE_MB,
            "output_dir": str(cls.OUTPUT_DIR),
            "log_dir": str(cls.LOG_DIR),
            "strict_mode": cls.STRICT_MODE,
            "allow_zero_amounts": cls.ALLOW_ZERO_AMOUNTS,
            "max_transaction_amount": cls.MAX_TRANSACTION_AMOUNT,
            "balance_threshold": cls.BALANCE_THRESHOLD,
            "log_level": cls.LOG_LEVEL,
        }


# Create a singleton instance
config = Config()
