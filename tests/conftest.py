import hashlib


def _get_file_checksum(path: str) -> str:
    """Get MD5 checksum of a file."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _assert_file_unchanged(path: str, original_checksum: str) -> None:
    """Verify file has not changed by comparing checksums."""
    final_checksum = _get_file_checksum(path)
    assert final_checksum == original_checksum, "CSV was modified after undo"
