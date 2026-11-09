from dataclasses import dataclass
from datetime import date

from ._contexts import Context

SKIP_COUNT_RESET = 0
GLICKO_RATING_DEFAULT = 1500
GLICKO_RD_DEFAULT = 350
GLICKO_RD_MIN = 45
GLICKO_RD_MAX = 500


@dataclass
class Dates:
    """Computed date attributes for a task."""

    latest_done_date: date
    latest_date: date
    recurrence_days: int
    due_date: date


@dataclass
class SyntheticOpponent:
    """An internal opponent built from the universe medians."""

    rating: int
    rating_deviation: int
    rating_date: date
    id: int | None = None


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
        rating: int = GLICKO_RATING_DEFAULT,
        rating_deviation: int = GLICKO_RD_DEFAULT,
        rating_date: date | None = None,
    ):
        self.id = id
        self.description = description
        self.context = context
        self.skip_count = skip_count
        self.starred = starred
        self.latest_done_date = dates.latest_done_date
        self.latest_date = dates.latest_date
        self.recurrence_days = dates.recurrence_days
        self.due_date = dates.due_date
        self.coins = coins
        self.rating = rating
        self.rating_deviation = rating_deviation
        self.rating_date = rating_date if rating_date is not None else dates.latest_done_date
