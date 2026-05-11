"""Core module for scheduling logic and internal pure functions."""

__version__ = "0.1.0"

# Data models
from .models import Context, Task  # noqa: F401

# Internal pure functions
from .compute import (  # noqa: F401
    compute_intervals,
    compute_latest_date,
    compute_recurrence_days,
    filter_due_contexts,
)

# I/O utilities
from .io import import_tasks_from_csv  # noqa: F401

# CLI
from .cli import app  # noqa: F401
