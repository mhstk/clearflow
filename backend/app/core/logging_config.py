"""
Logging configuration for the application.

Sets up structured logging to files with rotation and console output.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging():
    """
    Configure application-wide logging.

    Creates rotating log files in the logs/ directory:
    - app.log: General application logs
    - categorization.log: AI categorization specific logs
    - errors.log: Errors and exceptions only
    """
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear any existing handlers
    root_logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # Main application log file (rotating, 10MB max, keep 5 backups)
    app_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_handler)

    # Error log file (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "errors.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)

    # Categorization log file (for AI categorization tracking)
    categorization_logger = logging.getLogger("categorization")
    categorization_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "categorization.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    categorization_handler.setLevel(logging.INFO)
    categorization_handler.setFormatter(detailed_formatter)
    categorization_logger.addHandler(categorization_handler)

    # Log startup
    logging.info("=" * 80)
    logging.info("Application logging initialized")
    logging.info("=" * 80)


def get_categorization_logger():
    """Get the categorization-specific logger."""
    return logging.getLogger("categorization")
