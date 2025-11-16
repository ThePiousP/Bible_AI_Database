#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logging_config.py
Centralized logging configuration for the Bible NER pipeline

BEFORE (scattered throughout codebase):
  - print() statements everywhere
  - print(..., file=sys.stderr) for errors
  - No timestamps, no log levels
  - Can't control verbosity
  - No log files

AFTER (structured logging):
  - Consistent logging across all modules
  - Configurable log levels (DEBUG, INFO, WARN, ERROR)
  - Rotating file handlers
  - Timestamps on all messages
  - Color-coded console output
  - Easy to redirect to files

Created: 2025-10-29 (Phase 1 Refactoring)

Usage:
    # In any script:
    from code.utils.logging_config import setup_logging

    logger = setup_logging(__name__)
    logger.info("Starting process...")
    logger.error("Something went wrong", exc_info=True)

Migration from old code:
    # BEFORE:
    print(f"Processing {book_name}...")
    print(f"ERROR: Failed to load {filename}", file=sys.stderr)

    # AFTER:
    logger.info(f"Processing {book_name}...")
    logger.error(f"Failed to load {filename}")
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# ============================================================================
# Color Codes for Console Output (Windows & Unix compatible)
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output.
    Colors are applied based on log level.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to levelname
        if sys.stdout.isatty():  # Only colorize if output is to terminal
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
    file_level: Optional[int] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up structured logging for the Bible NER pipeline.

    Args:
        name: Logger name (use __name__ from calling module)
        level: Console log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional, creates rotating handler)
        console: Whether to log to console (default: True)
        file_level: File log level (default: DEBUG, captures everything)
        format_string: Custom format string (optional)

    Returns:
        Configured logger instance

    Example:
        # Basic usage:
        logger = setup_logging(__name__)
        logger.info("Processing started")

        # With file logging:
        logger = setup_logging(__name__, log_file="output/LOGS/export.log")

        # Debug mode:
        logger = setup_logging(__name__, level=logging.DEBUG)

    Comparison to old code:
        # BEFORE:
        print(f"INFO: Processing {book_name}...")
        print(f"ERROR: Failed to load {filename}", file=sys.stderr)

        # AFTER:
        logger.info(f"Processing {book_name}...")
        logger.error(f"Failed to load {filename}")
    """

    # Create logger
    logger = logging.getLogger(name or 'bible_ner')
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers filter

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Default format string
    if format_string is None:
        format_string = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'

    date_format = '%Y-%m-%d %H:%M:%S'

    # ========================================================================
    # Console Handler (colored output)
    # ========================================================================

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Use colored formatter for console
        console_formatter = ColoredFormatter(
            fmt=format_string,
            datefmt=date_format
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # ========================================================================
    # File Handler (rotating, captures all debug info)
    # ========================================================================

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler (max 10 MB per file, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )

        # File gets more detailed logs (default: DEBUG level)
        file_handler.setLevel(file_level or logging.DEBUG)

        # More detailed format for files (includes line numbers)
        file_format = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt=date_format
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# ============================================================================
# Context Manager for Temporary Log Level Changes
# ============================================================================

class LogLevel:
    """
    Context manager for temporarily changing log level.

    Example:
        logger = setup_logging(__name__)

        # Normal logging
        logger.info("This shows")

        # Temporarily enable debug
        with LogLevel(logger, logging.DEBUG):
            logger.debug("This also shows")

        # Back to normal
        logger.debug("This doesn't show")
    """

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.new_level = level
        self.old_level = logger.level

    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, *args):
        self.logger.setLevel(self.old_level)


# ============================================================================
# Convenience Functions
# ============================================================================

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a logger (convenience wrapper).

    Example:
        from code.utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Hello, world!")
    """
    return setup_logging(name=name, level=level)


def enable_debug_logging():
    """
    Enable DEBUG level for all loggers in the bible_ner hierarchy.

    Call this early in your script to see detailed debug output:

    Example:
        from code.utils.logging_config import enable_debug_logging

        enable_debug_logging()  # Now all loggers show DEBUG messages
    """
    logging.getLogger('bible_ner').setLevel(logging.DEBUG)


def disable_external_loggers():
    """
    Silence noisy third-party loggers (requests, urllib3, etc.).

    Call this to reduce log spam from external libraries:

    Example:
        from code.utils.logging_config import disable_external_loggers

        disable_external_loggers()  # Quiets requests, urllib3, etc.
    """
    noisy_loggers = [
        'urllib3',
        'requests',
        'urllib3.connectionpool',
        'charset_normalizer',
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


# ============================================================================
# Script-specific logger factories
# ============================================================================

def setup_script_logger(
    script_name: str,
    log_dir: str = "output/LOGS",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up logger for a script with automatic file logging.

    Creates a log file named: {log_dir}/{script_name}_{timestamp}.log

    Example:
        # In export_ner_silver.py:
        logger = setup_script_logger('export_ner_silver')
        logger.info("Starting export...")

        # Creates: output/LOGS/export_ner_silver_2025-10-29_14-30-45.log
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = f"{log_dir}/{script_name}_{timestamp}.log"

    return setup_logging(
        name=script_name,
        level=level,
        log_file=log_file,
        console=True
    )


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Example 1: Basic console logging
    logger = setup_logging(__name__)
    logger.debug("This won't show (level=INFO by default)")
    logger.info("Processing started")
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Example 2: Debug mode
    print("\n--- Debug Mode ---")
    debug_logger = setup_logging(__name__, level=logging.DEBUG)
    debug_logger.debug("Now you can see debug messages!")
    debug_logger.info("And info messages")

    # Example 3: File logging
    print("\n--- File Logging ---")
    file_logger = setup_logging(
        __name__,
        level=logging.INFO,
        log_file="output/LOGS/test.log"
    )
    file_logger.info("This goes to both console and file")
    file_logger.debug("This only goes to file (not console)")
    print("✓ Log file created at: output/LOGS/test.log")

    # Example 4: Context manager for temporary debug
    print("\n--- Temporary Debug Level ---")
    logger = setup_logging(__name__)
    logger.debug("This won't show")

    with LogLevel(logger, logging.DEBUG):
        logger.debug("This shows during context")

    logger.debug("This won't show again")

    # Example 5: Exception logging
    print("\n--- Exception Logging ---")
    logger = setup_logging(__name__)
    try:
        raise ValueError("Something went wrong!")
    except Exception as e:
        logger.error("Caught exception", exc_info=True)  # Includes stack trace

    print("\n✓ All logging examples completed!")
    print("\nMigration tips:")
    print("  - Replace print() with logger.info()")
    print("  - Replace print(..., file=sys.stderr) with logger.error()")
    print("  - Use logger.debug() for verbose diagnostic output")
    print("  - Use exc_info=True to include stack traces")
