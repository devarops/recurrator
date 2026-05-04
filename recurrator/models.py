from dataclasses import dataclass
from datetime import date
from enum import Enum

SKIP_COUNT_RESET = 0


class Context(Enum):
    """Valid task contexts."""

    CASA = "casa"
    LAPTOP = "laptop"
    LIMPIAR = "limpiar"


@dataclass
class ComputedDates:
    """Computed date attributes for a task."""

    latest_date: date
    recurrence_days: int
    due_date: date


class Task:
    """Represents a task imported from CSV."""

    def __init__(
        self,
        id: int,
        description: str,
        context: Context,
        skip_count: int,
        starred: bool,
        computed_dates: ComputedDates,
    ):
        self.id = id
        self.description = description
        self.context = context
        self.skip_count = skip_count
        self.starred = starred
        self.latest_date = computed_dates.latest_date
        self.recurrence_days = computed_dates.recurrence_days
        self.due_date = computed_dates.due_date
