from datetime import date


def compute_intervals(dates: list[date]) -> list[int]:
    intervals = []
    for i in range(1, len(dates)):
        delta = dates[i] - dates[i - 1]
        intervals.append(delta.days)
    return intervals
