"""Durable bindings between jobs, preparations, and external calendar events."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


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
    """Locked append-only booking store with legacy-read compatibility."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="booking-record", version=1)

    def create(self, record: BookingRecord) -> BookingRecord:
        payload = asdict(record)
        payload["start"] = record.start.isoformat()
        payload["end"] = record.end.isoformat()
        with self._storage.locked_file.locked():
            existing = self._find_unlocked("idempotency_key", record.idempotency_key)
            if existing is not None:
                if existing != record:
                    raise ValueError("idempotency key already bound to another booking")
                return existing
            if self._find_unlocked("booking_id", record.booking_id) is not None:
                raise ValueError(f"booking already exists: {record.booking_id}")
            self._append_unlocked(payload)
        return record

    def get(self, booking_id: str) -> BookingRecord | None:
        with self._storage.locked_file.locked():
            return self._find_unlocked("booking_id", booking_id)

    def get_by_idempotency_key(self, key: str) -> BookingRecord | None:
        with self._storage.locked_file.locked():
            return self._find_unlocked("idempotency_key", key)

    def _find_unlocked(self, field: str, value: str) -> BookingRecord | None:
        found: BookingRecord | None = None
        for payload in self._storage._read_all_unlocked():
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

    def _append_unlocked(self, payload: dict[str, object]) -> None:
        import json, os
        envelope = {
            "_schema": self._storage.schema,
            "_version": self._storage.version,
            "data": payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
