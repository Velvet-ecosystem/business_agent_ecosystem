"""Locked production stores for append-once lifecycle artifacts."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from business_agents.bookings import BookingPreparation
from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.delivery_records import DeliveryRecord
from business_agents.notifications import NotificationDraft
from business_agents.work_start import WorkStartRecord


class LockedBookingPreparationStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="booking-preparation")

    def create(self, record: BookingPreparation) -> BookingPreparation:
        payload = asdict(record)
        payload["start"] = record.start.isoformat()
        payload["end"] = record.end.isoformat()
        payload["metadata"] = None if record.metadata is None else dict(record.metadata)
        self._storage.append_unique(payload, field="preparation_id")
        return record

    def get(self, preparation_id: str) -> BookingPreparation | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("preparation_id") == preparation_id:
                metadata = payload.get("metadata")
                return BookingPreparation(
                    preparation_id=str(payload["preparation_id"]),
                    proposal_id=str(payload["proposal_id"]),
                    job_id=str(payload["job_id"]),
                    selected_index=int(payload["selected_index"]),
                    start=datetime.fromisoformat(str(payload["start"])),
                    end=datetime.fromisoformat(str(payload["end"])),
                    timezone=str(payload["timezone"]),
                    notes=str(payload.get("notes", "")),
                    metadata=None if metadata is None else dict(metadata),
                )
        return None


class LockedNotificationDraftStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="notification-draft")

    def create(self, draft: NotificationDraft) -> NotificationDraft:
        self._storage.append_unique(asdict(draft), field="draft_id")
        return draft

    def get(self, draft_id: str) -> NotificationDraft | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("draft_id") == draft_id:
                return NotificationDraft(**payload)
        return None


class LockedDeliveryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="delivery-record")

    def create(self, record: DeliveryRecord) -> DeliveryRecord:
        with self._storage.locked_file.locked():
            items = self._storage._read_all_unlocked()
            for payload in items:
                if payload.get("idempotency_key") == record.idempotency_key:
                    existing = DeliveryRecord(**payload)
                    if existing != record:
                        raise ValueError("idempotency key already bound to another delivery")
                    return existing
            if any(payload.get("delivery_id") == record.delivery_id for payload in items):
                raise ValueError(f"delivery already exists: {record.delivery_id}")
            self._append_unlocked(asdict(record))
        return record

    def get(self, delivery_id: str) -> DeliveryRecord | None:
        return self._find("delivery_id", delivery_id)

    def get_by_idempotency_key(self, key: str) -> DeliveryRecord | None:
        return self._find("idempotency_key", key)

    def _find(self, field: str, value: str) -> DeliveryRecord | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get(field) == value:
                return DeliveryRecord(**payload)
        return None

    def _append_unlocked(self, payload: dict[str, object]) -> None:
        import json, os
        envelope = {"_schema": "delivery-record", "_version": 1, "data": payload}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


class LockedWorkStartStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="work-start-record")

    def create(self, record: WorkStartRecord) -> WorkStartRecord:
        with self._storage.locked_file.locked():
            items = self._storage._read_all_unlocked()
            if any(payload.get("start_id") == record.start_id for payload in items):
                raise ValueError(f"work start already exists: {record.start_id}")
            if any(payload.get("job_id") == record.job_id for payload in items):
                raise ValueError(f"job already started: {record.job_id}")
            self._append_unlocked(asdict(record))
        return record

    def get(self, start_id: str) -> WorkStartRecord | None:
        return self._find("start_id", start_id)

    def get_by_job(self, job_id: str) -> WorkStartRecord | None:
        return self._find("job_id", job_id)

    def _find(self, field: str, value: str) -> WorkStartRecord | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get(field) == value:
                return WorkStartRecord(**payload)
        return None

    def _append_unlocked(self, payload: dict[str, object]) -> None:
        import json, os
        envelope = {"_schema": "work-start-record", "_version": 1, "data": payload}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
