"""
Logging configuration for the application.

Sets up structured logging:
- Production (Vercel): Console only (read-only filesystem)
- Development: Console + rotating file logs
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging():
    """
    Configure application-wide logging.

    In production (Vercel): Console logging only
    In development: Console + rotating log files in logs/ directory
    """
    # Check if running in production (Vercel has read-only filesystem)
    is_production = os.environ.get("ENV", "development").lower() == "production"

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

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter if is_production else detailed_formatter)
    root_logger.addHandler(console_handler)

    # File handlers only in development (Vercel has read-only filesystem)
    if not is_production:
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)

            # Main application log file
            app_handler = logging.handlers.RotatingFileHandler(
                logs_dir / "app.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            )
            app_handler.setLevel(logging.INFO)
            app_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(app_handler)

            # Error log file
            error_handler = logging.handlers.RotatingFileHandler(
                logs_dir / "errors.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(error_handler)

            # Categorization log file
            categorization_logger = logging.getLogger("categorization")
            categorization_handler = logging.handlers.RotatingFileHandler(
                logs_dir / "categorization.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            )
            categorization_handler.setLevel(logging.INFO)
            categorization_handler.setFormatter(detailed_formatter)
            categorization_logger.addHandler(categorization_handler)
        except OSError:
            # Filesystem might be read-only, skip file logging
            pass

    # Log startup
    logging.info("Logging initialized (production=%s)", is_production)


def get_categorization_logger():
    """Get the categorization-specific logger."""
    return logging.getLogger("categorization")
