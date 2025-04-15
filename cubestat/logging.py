"""Logging configuration for cubestat."""

import logging
import os
import sys
from typing import Optional


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> None:
    """Configure logging for cubestat.
    
    Args:
        level: The logging level
        log_file: Path to log file, if None, logs are only sent to console
        console: Whether to log to console
    """
    logger = logging.getLogger("cubestat")
    logger.setLevel(level)
    logger.handlers = []  # Remove existing handlers
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Add file handler if log_file is specified
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            print(f"Error setting up log file: {e}", file=sys.stderr)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)