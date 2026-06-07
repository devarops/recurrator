from dataclasses import dataclass
from datetime import date

from ._contexts import Context

SKIP_COUNT_RESET = 0


@dataclass
class Dates:
    """Computed date attributes for a task."""

    latest_date: date
    recurrence_days: int
    due_date: date
    latest_done_date: date | None = None


class Task:
    """Represents a task imported from CSV."""

    def __init__(
        self,
        id: int,
        description: str,
        context: Context,
        skip_count: int,
        starred: bool,
        dates: Dates,
        coins: int,
    ):
        self.id = id
        self.description = description
        self.context = context
        self.skip_count = skip_count
        self.starred = starred
        self.latest_date = dates.latest_date
        self.recurrence_days = dates.recurrence_days
        self.due_date = dates.due_date
        self.latest_done_date = dates.latest_done_date
        self.coins = coins
