"""Durable booking preparation records bound to stored schedule proposals."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class BookingPreparation:
    preparation_id: str
    proposal_id: str
    job_id: str
    selected_index: int
    start: datetime
    end: datetime
    timezone: str
    notes: str = ""
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("preparation_id", self.preparation_id),
            ("proposal_id", self.proposal_id),
            ("job_id", self.job_id),
            ("timezone", self.timezone),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.selected_index, int) or isinstance(self.selected_index, bool):
            raise ValueError("selected_index must be an integer")
        if self.selected_index < 0:
            raise ValueError("selected_index must be non-negative")
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("booking preparation times must be timezone-aware")
        if self.end <= self.start:
            raise ValueError("booking preparation end must be after start")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")


class JsonlBookingPreparationStore:
    """Append-only store for exact-window booking preparation records."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, record: BookingPreparation) -> BookingPreparation:
        if self.get(record.preparation_id) is not None:
            raise ValueError(f"booking preparation already exists: {record.preparation_id}")
        payload = asdict(record)
        payload["start"] = record.start.isoformat()
        payload["end"] = record.end.isoformat()
        payload["metadata"] = dict(record.metadata or {})
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        return record

    def get(self, preparation_id: str) -> BookingPreparation | None:
        if not self.path.exists():
            return None
        found: BookingPreparation | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid booking preparation at line {line_number}") from exc
                if payload.get("preparation_id") == preparation_id:
                    found = BookingPreparation(
                        preparation_id=str(payload["preparation_id"]),
                        proposal_id=str(payload["proposal_id"]),
                        job_id=str(payload["job_id"]),
                        selected_index=int(payload["selected_index"]),
                        start=datetime.fromisoformat(str(payload["start"])),
                        end=datetime.fromisoformat(str(payload["end"])),
                        timezone=str(payload["timezone"]),
                        notes=str(payload.get("notes", "")),
                        metadata=dict(payload.get("metadata", {})),
                    )
        return found
