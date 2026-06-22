import os
import time
from pathlib import Path

import pytest

from business_agents.gateway.file_lock import LocalFileLock


def test_lock_is_created_and_removed(tmp_path: Path) -> None:
    path = tmp_path / "receipts.lock"

    with LocalFileLock(path):
        assert path.exists()

    assert not path.exists()


def test_lock_contention_times_out(tmp_path: Path) -> None:
    path = tmp_path / "receipts.lock"

    with LocalFileLock(path):
        with pytest.raises(TimeoutError, match="timed out waiting for lock"):
            with LocalFileLock(path, timeout=0.01, poll_interval=0.005):
                pass


def test_stale_lock_is_recovered(tmp_path: Path) -> None:
    path = tmp_path / "receipts.lock"
    path.write_text("stale", encoding="utf-8")
    old = time.time() - 120
    os.utime(path, (old, old))

    with LocalFileLock(path, stale_after=60):
        assert path.exists()

    assert not path.exists()


def test_lock_releases_after_exception(tmp_path: Path) -> None:
    path = tmp_path / "receipts.lock"

    with pytest.raises(RuntimeError, match="boom"):
        with LocalFileLock(path):
            raise RuntimeError("boom")

    assert not path.exists()
