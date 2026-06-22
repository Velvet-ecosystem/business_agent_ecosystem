"""Small local lock-file helper for single-writer receipt logs."""

from __future__ import annotations

import os
import time
from contextlib import AbstractContextManager
from pathlib import Path
from types import TracebackType


class LocalFileLock(AbstractContextManager["LocalFileLock"]):
    """Acquire an adjacent lock file using atomic creation.

    This is intended for one host and one local filesystem. A stale lock may be
    removed after ``stale_after`` seconds.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        timeout: float = 5.0,
        poll_interval: float = 0.05,
        stale_after: float = 60.0,
    ) -> None:
        if timeout < 0:
            raise ValueError("timeout must be non-negative")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        if stale_after <= 0:
            raise ValueError("stale_after must be positive")

        self.path = Path(path)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.stale_after = stale_after
        self._acquired = False

    def acquire(self) -> None:
        deadline = time.monotonic() + self.timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                descriptor = os.open(
                    self.path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
            except FileExistsError:
                if self._is_stale():
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    continue

                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out waiting for lock: {self.path}")
                time.sleep(self.poll_interval)
                continue

            try:
                payload = f"pid={os.getpid()} created={time.time()}\n".encode("utf-8")
                os.write(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

            self._acquired = True
            return

    def release(self) -> None:
        if not self._acquired:
            return
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        finally:
            self._acquired = False

    def _is_stale(self) -> bool:
        try:
            age = time.time() - self.path.stat().st_mtime
        except FileNotFoundError:
            return False
        return age >= self.stale_after

    def __enter__(self) -> "LocalFileLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()
