"""Core foundation package for ResearchOS."""

from backend.core.app import create_app
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger, setup_logging
from backend.core.models import (
    Citation,
    Evidence,
    Experiment,
    ResearchPlan,
    ResearchQuestion,
    ResearchResult,
    ResearchTask,
    Source,
)

__all__ = [
    "Citation",
    "Evidence",
    "Experiment",
    "ResearchPlan",
    "ResearchQuestion",
    "ResearchResult",
    "ResearchTask",
    "Settings",
    "Source",
    "create_app",
    "get_logger",
    "get_settings",
    "setup_logging",
]
