"""Append-only receiving inspection records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from business_agents.compatible_storage import CompatibleLockedJsonlFile


class InspectionStatus(str, Enum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs-review"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReceivingInspection:
    inspection_id: str
    evidence_id: str
    artifact_id: str
    status: InspectionStatus
    quantity_expected: int
    quantity_received: int
    supplier_part_expected: str
    supplier_part_received: str
    manufacturer_part_expected: str
    manufacturer_part_received: str
    inspected_at: str
    inspected_by: str
    findings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "inspection_id",
            "evidence_id",
            "artifact_id",
            "supplier_part_expected",
            "supplier_part_received",
            "manufacturer_part_expected",
            "manufacturer_part_received",
            "inspected_at",
            "inspected_by",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.status, InspectionStatus):
            raise ValueError("status must be an InspectionStatus")
        for name in ("quantity_expected", "quantity_received"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{name} must be an integer")
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if not isinstance(self.findings, tuple):
            raise ValueError("findings must be a tuple")
        for finding in self.findings:
            if not isinstance(finding, str) or not finding.strip():
                raise ValueError("findings must contain non-empty strings")
        if self.status is InspectionStatus.MATCHED and self.findings:
            raise ValueError("matched inspections must not carry findings")
        if self.status is not InspectionStatus.MATCHED and not self.findings:
            raise ValueError("non-matched inspections require findings")

    @property
    def eligible_for_stock(self) -> bool:
        return False

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["findings"] = list(self.findings)
        data["eligible_for_stock"] = self.eligible_for_stock
        return data


class ReceivingInspectionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._storage = CompatibleLockedJsonlFile(
            self.path, schema="receiving-inspection", version=1
        )

    def add(self, inspection: ReceivingInspection) -> ReceivingInspection:
        self._storage.append_unique(inspection.payload(), field="inspection_id")
        return inspection

    def get(self, inspection_id: str) -> ReceivingInspection | None:
        if not isinstance(inspection_id, str) or not inspection_id.strip():
            raise ValueError("inspection_id must be a non-empty string")
        for data in reversed(self._storage.read_all()):
            if data.get("inspection_id") == inspection_id:
                return self._from_payload(data)
        return None

    def list_for_evidence(self, evidence_id: str) -> tuple[ReceivingInspection, ...]:
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("evidence_id must be a non-empty string")
        matches = [
            self._from_payload(data)
            for data in self._storage.read_all()
            if data.get("evidence_id") == evidence_id
        ]
        return tuple(matches)

    @staticmethod
    def _from_payload(data: Mapping[str, Any]) -> ReceivingInspection:
        payload = dict(data)
        payload.pop("eligible_for_stock", None)
        status = payload.get("status")
        if isinstance(status, str):
            payload["status"] = InspectionStatus(status)
        findings = payload.get("findings", ())
        if isinstance(findings, list):
            payload["findings"] = tuple(findings)
        return ReceivingInspection(**payload)
