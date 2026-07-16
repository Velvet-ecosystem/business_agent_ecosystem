"""Append-only quarantine records for receiving discrepancies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from business_agents.compatible_storage import CompatibleLockedJsonlFile


class QuarantineStatus(str, Enum):
    HELD_FOR_REVIEW = "held-for-review"
    REJECTED = "rejected"
    RELEASE_REVIEW_REQUIRED = "release-review-required"


@dataclass(frozen=True)
class ReceivingQuarantine:
    quarantine_id: str
    inspection_id: str
    evidence_id: str
    artifact_id: str
    status: QuarantineStatus
    reason_codes: tuple[str, ...]
    held_at: str
    held_by: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "quarantine_id",
            "inspection_id",
            "evidence_id",
            "artifact_id",
            "held_at",
            "held_by",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.status, QuarantineStatus):
            raise ValueError("status must be a QuarantineStatus")
        if not isinstance(self.reason_codes, tuple) or not self.reason_codes:
            raise ValueError("reason_codes must be a non-empty tuple")
        for code in self.reason_codes:
            if not isinstance(code, str) or not code.strip():
                raise ValueError("reason_codes must contain non-empty strings")
        if not isinstance(self.notes, tuple):
            raise ValueError("notes must be a tuple")
        for note in self.notes:
            if not isinstance(note, str) or not note.strip():
                raise ValueError("notes must contain non-empty strings")

    @property
    def eligible_for_stock(self) -> bool:
        return False

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["reason_codes"] = list(self.reason_codes)
        data["notes"] = list(self.notes)
        data["eligible_for_stock"] = self.eligible_for_stock
        return data


class ReceivingQuarantineStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._storage = CompatibleLockedJsonlFile(
            self.path, schema="receiving-quarantine", version=1
        )

    def add(self, quarantine: ReceivingQuarantine) -> ReceivingQuarantine:
        self._storage.append_unique(quarantine.payload(), field="quarantine_id")
        return quarantine

    def get(self, quarantine_id: str) -> ReceivingQuarantine | None:
        if not isinstance(quarantine_id, str) or not quarantine_id.strip():
            raise ValueError("quarantine_id must be a non-empty string")
        for data in reversed(self._storage.read_all()):
            if data.get("quarantine_id") == quarantine_id:
                return self._from_payload(data)
        return None

    def list_for_inspection(self, inspection_id: str) -> tuple[ReceivingQuarantine, ...]:
        if not isinstance(inspection_id, str) or not inspection_id.strip():
            raise ValueError("inspection_id must be a non-empty string")
        matches = [
            self._from_payload(data)
            for data in self._storage.read_all()
            if data.get("inspection_id") == inspection_id
        ]
        return tuple(matches)

    @staticmethod
    def _from_payload(data: Mapping[str, Any]) -> ReceivingQuarantine:
        payload = dict(data)
        payload.pop("eligible_for_stock", None)
        status = payload.get("status")
        if isinstance(status, str):
            payload["status"] = QuarantineStatus(status)
        for field in ("reason_codes", "notes"):
            value = payload.get(field, ())
            if isinstance(value, list):
                payload[field] = tuple(value)
        return ReceivingQuarantine(**payload)
