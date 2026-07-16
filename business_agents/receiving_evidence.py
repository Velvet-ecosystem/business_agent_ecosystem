"""Append-only receiving evidence records for future procurement verification."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class ReceivingEvidence:
    evidence_id: str
    artifact_id: str
    received_reference: str
    carrier_reference: str
    package_condition: str
    claimed_supplier_name: str
    claimed_supplier_part_number: str
    claimed_manufacturer_part_number: str
    quantity_received: int
    received_at: str
    received_by: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "artifact_id",
            "received_reference",
            "carrier_reference",
            "package_condition",
            "claimed_supplier_name",
            "claimed_supplier_part_number",
            "claimed_manufacturer_part_number",
            "received_at",
            "received_by",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.quantity_received, int) or isinstance(
            self.quantity_received, bool
        ):
            raise ValueError("quantity_received must be an integer")
        if self.quantity_received <= 0:
            raise ValueError("quantity_received must be positive")
        if not isinstance(self.notes, tuple):
            raise ValueError("notes must be a tuple")
        for note in self.notes:
            if not isinstance(note, str) or not note.strip():
                raise ValueError("notes must contain non-empty strings")

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["notes"] = list(self.notes)
        return data


class ReceivingEvidenceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._storage = CompatibleLockedJsonlFile(
            self.path, schema="receiving-evidence", version=1
        )

    def add(self, evidence: ReceivingEvidence) -> ReceivingEvidence:
        self._storage.append_unique(evidence.payload(), unique_key="evidence_id")
        return evidence

    def get(self, evidence_id: str) -> ReceivingEvidence | None:
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("evidence_id must be a non-empty string")
        for data in reversed(self._storage.read_all()):
            if data.get("evidence_id") == evidence_id:
                return self._from_payload(data)
        return None

    def list_for_artifact(self, artifact_id: str) -> tuple[ReceivingEvidence, ...]:
        if not isinstance(artifact_id, str) or not artifact_id.strip():
            raise ValueError("artifact_id must be a non-empty string")
        matches = [
            self._from_payload(data)
            for data in self._storage.read_all()
            if data.get("artifact_id") == artifact_id
        ]
        return tuple(matches)

    @staticmethod
    def _from_payload(data: Mapping[str, Any]) -> ReceivingEvidence:
        payload = dict(data)
        notes = payload.get("notes", ())
        if isinstance(notes, list):
            payload["notes"] = tuple(notes)
        return ReceivingEvidence(**payload)
