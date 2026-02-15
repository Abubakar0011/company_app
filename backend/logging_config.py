"""
Centralized logging configuration for the application.
Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from config import config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure logging for the entire application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name (will be placed in LOG_DIR)
        console_output: Whether to output to console
    
    Returns:
        Configured logger instance
    """
    # Use config log level if not specified
    if log_level is None:
        log_level = config.LOG_LEVEL
    
    # Ensure log directory exists
    config.ensure_directories()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        log_path = config.get_log_path(log_file)
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set logging level for third-party libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize default logging on module import
setup_logging(log_file="transaction_extractor.log")
