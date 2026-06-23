"""Durable records for explicit work-start ceremonies."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkStartRecord:
    start_id: str
    job_id: str
    booking_id: str
    started_by: str
    reason: str

    def __post_init__(self) -> None:
        for name, value in (
            ("start_id", self.start_id),
            ("job_id", self.job_id),
            ("booking_id", self.booking_id),
            ("started_by", self.started_by),
            ("reason", self.reason),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.reason) > 2000:
            raise ValueError("reason is too long")


class JsonlWorkStartStore:
    """Append-only store for one work-start record per job."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, record: WorkStartRecord) -> WorkStartRecord:
        if self.get(record.start_id) is not None:
            raise ValueError(f"work start already exists: {record.start_id}")
        existing = self.get_by_job(record.job_id)
        if existing is not None:
            raise ValueError(f"job already started: {record.job_id}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True, ensure_ascii=False) + "\n")
        return record

    def get(self, start_id: str) -> WorkStartRecord | None:
        return self._find("start_id", start_id)

    def get_by_job(self, job_id: str) -> WorkStartRecord | None:
        return self._find("job_id", job_id)

    def _find(self, field: str, value: str) -> WorkStartRecord | None:
        if not self.path.exists():
            return None
        found: WorkStartRecord | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid work-start record at line {line_number}") from exc
                if payload.get(field) == value:
                    found = WorkStartRecord(**payload)
        return found
