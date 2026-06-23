"""Durable bindings between jobs, preparations, and external calendar events."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class BookingRecord:
    booking_id: str
    job_id: str
    preparation_id: str
    idempotency_key: str
    event_id: str
    start: datetime
    end: datetime
    timezone: str

    def __post_init__(self) -> None:
        for name, value in (
            ("booking_id", self.booking_id),
            ("job_id", self.job_id),
            ("preparation_id", self.preparation_id),
            ("idempotency_key", self.idempotency_key),
            ("event_id", self.event_id),
            ("timezone", self.timezone),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("booking times must be timezone-aware")
        if self.end <= self.start:
            raise ValueError("booking end must be after start")


class JsonlBookingStore:
    """Append-only external booking binding store."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, record: BookingRecord) -> BookingRecord:
        existing = self.get_by_idempotency_key(record.idempotency_key)
        if existing is not None:
            if existing != record:
                raise ValueError("idempotency key already bound to another booking")
            return existing
        if self.get(record.booking_id) is not None:
            raise ValueError(f"booking already exists: {record.booking_id}")
        payload = asdict(record)
        payload["start"] = record.start.isoformat()
        payload["end"] = record.end.isoformat()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        return record

    def get(self, booking_id: str) -> BookingRecord | None:
        return self._find("booking_id", booking_id)

    def get_by_idempotency_key(self, key: str) -> BookingRecord | None:
        return self._find("idempotency_key", key)

    def _find(self, field: str, value: str) -> BookingRecord | None:
        if not self.path.exists():
            return None
        found: BookingRecord | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid booking record at line {line_number}") from exc
                if payload.get(field) == value:
                    found = BookingRecord(
                        booking_id=str(payload["booking_id"]),
                        job_id=str(payload["job_id"]),
                        preparation_id=str(payload["preparation_id"]),
                        idempotency_key=str(payload["idempotency_key"]),
                        event_id=str(payload["event_id"]),
                        start=datetime.fromisoformat(str(payload["start"])),
                        end=datetime.fromisoformat(str(payload["end"])),
                        timezone=str(payload["timezone"]),
                    )
        return found
