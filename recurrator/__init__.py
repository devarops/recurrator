"""Core module for scheduling logic and internal pure functions."""

__version__ = "0.1.0"

# Data models
from .models import Context, Task

# Internal pure functions
from .compute import compute_intervals, compute_latest_date, compute_recurrence_days

# I/O utilities
from .io import import_tasks_from_csv
from . import io

# CLI
from .cli import app
