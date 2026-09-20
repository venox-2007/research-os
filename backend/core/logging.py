"""Structured application logging for ResearchOS.

Configures unified logging with module context, consistent formatting,
and configurable log levels.
"""

import logging
import sys


def setup_logging(log_level: str = "INFO", logger_name: str | None = None) -> logging.Logger:
    """Set up and return a configured logger instance.

    Args:
        log_level: Desired log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        logger_name: Optional name for a specific logger; defaults to 'research_os'.

    Returns:
        Configured logging.Logger.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger(logger_name or "research_os")
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger with hierarchical namespace under 'research_os'."""
    return logging.getLogger(f"research_os.{name}")
