"""Decision records for stock eligibility design.

These records only express whether a received item is eligible for a later
inventory step. They do not mutate stock and do not release inventory.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.receiving_verification import ReceivingVerification


class StockEligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not-eligible"
    REVIEW_REQUIRED = "review-required"


@dataclass(frozen=True)
class StockEligibilityDecision:
    decision_id: str
    verification_reason: str
    artifact_id: str
    evidence_id: str
    inspection_id: str
    status: StockEligibilityStatus
    decided_at: str
    decided_by: str
    reason_codes: tuple[str, ...]
    quarantine_id: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "decision_id",
            "verification_reason",
            "artifact_id",
            "evidence_id",
            "inspection_id",
            "decided_at",
            "decided_by",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.quarantine_id is not None and (
            not isinstance(self.quarantine_id, str) or not self.quarantine_id.strip()
        ):
            raise ValueError("quarantine_id must be None or a non-empty string")
        if not isinstance(self.status, StockEligibilityStatus):
            raise ValueError("status must be a StockEligibilityStatus")
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
    def mutates_stock(self) -> bool:
        return False

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["reason_codes"] = list(self.reason_codes)
        data["notes"] = list(self.notes)
        data["mutates_stock"] = self.mutates_stock
        return data


class StockEligibilityStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._storage = CompatibleLockedJsonlFile(
            self.path, schema="stock-eligibility", version=1
        )

    def add(self, decision: StockEligibilityDecision) -> StockEligibilityDecision:
        self._storage.append_unique(decision.payload(), field="decision_id")
        return decision

    def get(self, decision_id: str) -> StockEligibilityDecision | None:
        if not isinstance(decision_id, str) or not decision_id.strip():
            raise ValueError("decision_id must be a non-empty string")
        for data in reversed(self._storage.read_all()):
            if data.get("decision_id") == decision_id:
                return self._from_payload(data)
        return None

    def list_for_evidence(self, evidence_id: str) -> tuple[StockEligibilityDecision, ...]:
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("evidence_id must be a non-empty string")
        matches = [
            self._from_payload(data)
            for data in self._storage.read_all()
            if data.get("evidence_id") == evidence_id
        ]
        return tuple(matches)

    @staticmethod
    def _from_payload(data: Mapping[str, Any]) -> StockEligibilityDecision:
        payload = dict(data)
        payload.pop("mutates_stock", None)
        status = payload.get("status")
        if isinstance(status, str):
            payload["status"] = StockEligibilityStatus(status)
        for field in ("reason_codes", "notes"):
            value = payload.get(field, ())
            if isinstance(value, list):
                payload[field] = tuple(value)
        return StockEligibilityDecision(**payload)


def propose_stock_eligibility_decision(
    *,
    decision_id: str,
    verification: ReceivingVerification,
    artifact_id: str,
    evidence_id: str,
    inspection_id: str,
    decided_at: str,
    decided_by: str,
    quarantine_id: str | None = None,
    notes: tuple[str, ...] = (),
) -> StockEligibilityDecision:
    if not verification.passed:
        status = StockEligibilityStatus.NOT_ELIGIBLE
        reason_codes = (verification.reason,)
    elif verification.reason == "verified-matched-receiving-chain":
        status = StockEligibilityStatus.ELIGIBLE
        reason_codes = (verification.reason,)
    else:
        status = StockEligibilityStatus.REVIEW_REQUIRED
        reason_codes = (verification.reason,)

    return StockEligibilityDecision(
        decision_id=decision_id,
        verification_reason=verification.reason,
        artifact_id=artifact_id,
        evidence_id=evidence_id,
        inspection_id=inspection_id,
        quarantine_id=quarantine_id,
        status=status,
        decided_at=decided_at,
        decided_by=decided_by,
        reason_codes=reason_codes,
        notes=notes,
    )
