"""Compatibility-safe locked JSONL storage for gradual migrations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from business_agents.storage import JsonlCorruptionError, LockedJsonlFile


class CompatibleLockedJsonlFile:
    """Reads legacy raw records and new versioned envelopes under one lock."""

    def __init__(self, path: Path, *, schema: str, version: int = 1) -> None:
        self.locked_file = LockedJsonlFile(path, schema=schema, version=version)
        self.path = path
        self.schema = schema
        self.version = version

    def append(self, payload: Mapping[str, Any]) -> None:
        self.locked_file.append(payload)

    def read_all(self) -> list[dict[str, Any]]:
        with self.locked_file.locked():
            if not self.path.exists():
                return []
            records: list[dict[str, Any]] = []
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        item = json.loads(stripped)
                    except json.JSONDecodeError as exc:
                        raise JsonlCorruptionError(
                            f"invalid JSONL at {self.path}:{line_number}"
                        ) from exc
                    if not isinstance(item, dict):
                        raise JsonlCorruptionError(
                            f"record is not an object at {self.path}:{line_number}"
                        )
                    if "_schema" in item or "_version" in item or "data" in item:
                        if item.get("_schema") != self.schema:
                            raise JsonlCorruptionError(
                                f"unexpected schema at {self.path}:{line_number}"
                            )
                        if item.get("_version") != self.version:
                            raise JsonlCorruptionError(
                                f"unsupported version at {self.path}:{line_number}"
                            )
                        data = item.get("data")
                        if not isinstance(data, dict):
                            raise JsonlCorruptionError(
                                f"record data is not an object at {self.path}:{line_number}"
                            )
                        records.append(data)
                    else:
                        records.append(item)
            return records

    def append_unique(self, payload: Mapping[str, Any], *, field: str) -> None:
        value = payload.get(field)
        if value is None:
            raise ValueError(f"unique field is missing: {field}")
        with self.locked_file.locked():
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
                    item = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise JsonlCorruptionError(
                        f"invalid JSONL at {self.path}:{line_number}"
                    ) from exc
                if not isinstance(item, dict):
                    raise JsonlCorruptionError(
                        f"record is not an object at {self.path}:{line_number}"
                    )
                if "_schema" in item or "_version" in item or "data" in item:
                    if item.get("_schema") != self.schema or item.get("_version") != self.version:
                        raise JsonlCorruptionError(
                            f"invalid envelope at {self.path}:{line_number}"
                        )
                    data = item.get("data")
                    if not isinstance(data, dict):
                        raise JsonlCorruptionError(
                            f"record data is not an object at {self.path}:{line_number}"
                        )
                    records.append(data)
                else:
                    records.append(item)
        return records
