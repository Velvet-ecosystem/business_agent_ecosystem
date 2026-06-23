"""Shared process-safe JSONL persistence primitives."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping


class JsonlCorruptionError(ValueError):
    """Raised when an append-only store contains malformed data."""


class LockedJsonlFile:
    """Small locked append/read primitive with schema envelopes and fsync."""

    def __init__(self, path: Path, *, schema: str, version: int = 1) -> None:
        if not schema.strip():
            raise ValueError("schema is required")
        if version < 1:
            raise ValueError("version must be positive")
        self.path = path
        self.schema = schema
        self.version = version
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self) -> Iterator[None]:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                    os.fsync(handle.fileno())
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def append(self, payload: Mapping[str, Any]) -> None:
        envelope = {
            "_schema": self.schema,
            "_version": self.version,
            "data": dict(payload),
        }
        encoded = json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n"
        with self.locked():
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())

    def read_all(self) -> list[dict[str, Any]]:
        with self.locked():
            return self._read_all_unlocked()

    def append_unique(self, payload: Mapping[str, Any], *, field: str) -> None:
        value = payload.get(field)
        if value is None:
            raise ValueError(f"unique field is missing: {field}")
        with self.locked():
            existing = self._read_all_unlocked()
            if any(item.get(field) == value for item in existing):
                raise ValueError(f"record already exists for {field}: {value}")
            envelope = {
                "_schema": self.schema,
                "_version": self.version,
                "data": dict(payload),
            }
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def _read_all_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    envelope = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise JsonlCorruptionError(
                        f"invalid JSONL at {self.path}:{line_number}"
                    ) from exc
                if envelope.get("_schema") != self.schema:
                    raise JsonlCorruptionError(
                        f"unexpected schema at {self.path}:{line_number}"
                    )
                if envelope.get("_version") != self.version:
                    raise JsonlCorruptionError(
                        f"unsupported version at {self.path}:{line_number}"
                    )
                data = envelope.get("data")
                if not isinstance(data, dict):
                    raise JsonlCorruptionError(
                        f"record data is not an object at {self.path}:{line_number}"
                    )
                records.append(data)
        return records
