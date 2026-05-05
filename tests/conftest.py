import hashlib
from datetime import date

# Test data constants
TASK_2_ORIGINAL_DATES = [None, None, date(2024, 1, 8), date(2024, 12, 7)]
TASK_2_UPDATED_DATES = [None, None, date(2025, 2, 1), date(2025, 11, 2)]
TASK_2_COMPLETION_DATE = date(2025, 2, 28)
TASK_2_EXPECTED_AFTER_COMPLETION = [None, date(2024, 1, 8), date(2024, 12, 7), date(2025, 2, 28)]

TASK_5_ORIGINAL_DATES = [
    date(2024, 8, 26),
    date(2024, 10, 12),
    date(2025, 1, 31),
    date(2025, 3, 14),
]
TASK_5_COMPLETION_DATE = date(2026, 5, 4)
TASK_5_EXPECTED_AFTER_COMPLETION = [
    date(2024, 10, 12),
    date(2025, 1, 31),
    date(2025, 3, 14),
    date(2026, 5, 4),
]


def _get_file_checksum(path: str) -> str:
    """Get MD5 checksum of a file."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _assert_file_unchanged(path: str, original_checksum: str) -> None:
    """Verify file has not changed by comparing checksums."""
    final_checksum = _get_file_checksum(path)
    assert final_checksum == original_checksum, "CSV was modified after undo"
