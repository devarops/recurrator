"""Core module for scheduling logic and internal pure functions."""

__version__ = "0.1.0"

# Internal pure functions
from .compute import compute_intervals  # noqa

# I/O utilities
from .io import Context, Task, import_tasks_from_csv  # noqa
