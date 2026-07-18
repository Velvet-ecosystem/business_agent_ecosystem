"""Human release review records for future stock eligibility handling.

A release review records a bounded human decision about a stock eligibility
record. It does not mutate inventory and does not execute a release.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.stock_eligibility import (
    StockEligibilityDecision,
    StockEligibilityStatus,
)


class ReleaseReviewDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    NEEDS_MORE_EVIDENCE = "needs-more-evidence"


@dataclass(frozen=True)
class ReleaseReview:
    review_id: str
    stock_eligibility_decision_id: str
    artifact_id: str
    evidence_id: str
    inspection_id: str
    decision: ReleaseReviewDecision
    reviewed_at: str
    reviewed_by: str
    reason_codes: tuple[str, ...]
    quarantine_id: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "review_id",
            "stock_eligibility_decision_id",
            "artifact_id",
            "evidence_id",
            "inspection_id",
            "reviewed_at",
            "reviewed_by",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.quarantine_id is not None and (
            not isinstance(self.quarantine_id, str) or not self.quarantine_id.strip()
        ):
            raise ValueError("quarantine_id must be None or a non-empty string")
        if not isinstance(self.decision, ReleaseReviewDecision):
            raise ValueError("decision must be a ReleaseReviewDecision")
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

    @property
    def executes_release(self) -> bool:
        return False

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        data["reason_codes"] = list(self.reason_codes)
        data["notes"] = list(self.notes)
        data["mutates_stock"] = self.mutates_stock
        data["executes_release"] = self.executes_release
        return data


class ReleaseReviewStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._storage = CompatibleLockedJsonlFile(
            self.path, schema="release-review", version=1
        )

    def add(self, review: ReleaseReview) -> ReleaseReview:
        self._storage.append_unique(review.payload(), field="review_id")
        return review

    def get(self, review_id: str) -> ReleaseReview | None:
        if not isinstance(review_id, str) or not review_id.strip():
            raise ValueError("review_id must be a non-empty string")
        for data in reversed(self._storage.read_all()):
            if data.get("review_id") == review_id:
                return self._from_payload(data)
        return None

    def list_for_eligibility_decision(
        self, decision_id: str
    ) -> tuple[ReleaseReview, ...]:
        if not isinstance(decision_id, str) or not decision_id.strip():
            raise ValueError("decision_id must be a non-empty string")
        matches = [
            self._from_payload(data)
            for data in self._storage.read_all()
            if data.get("stock_eligibility_decision_id") == decision_id
        ]
        return tuple(matches)

    @staticmethod
    def _from_payload(data: Mapping[str, Any]) -> ReleaseReview:
        payload = dict(data)
        payload.pop("mutates_stock", None)
        payload.pop("executes_release", None)
        decision = payload.get("decision")
        if isinstance(decision, str):
            payload["decision"] = ReleaseReviewDecision(decision)
        for field in ("reason_codes", "notes"):
            value = payload.get(field, ())
            if isinstance(value, list):
                payload[field] = tuple(value)
        return ReleaseReview(**payload)


def propose_release_review(
    *,
    review_id: str,
    eligibility: StockEligibilityDecision,
    reviewed_at: str,
    reviewed_by: str,
    approve_eligible: bool = False,
    notes: tuple[str, ...] = (),
) -> ReleaseReview:
    if eligibility.status is StockEligibilityStatus.NOT_ELIGIBLE:
        decision = ReleaseReviewDecision.DENIED
        reason_codes = ("stock-not-eligible",)
    elif eligibility.status is StockEligibilityStatus.REVIEW_REQUIRED:
        decision = ReleaseReviewDecision.NEEDS_MORE_EVIDENCE
        reason_codes = ("stock-review-required",)
    elif approve_eligible:
        decision = ReleaseReviewDecision.APPROVED
        reason_codes = ("human-approved-eligible-record",)
    else:
        decision = ReleaseReviewDecision.NEEDS_MORE_EVIDENCE
        reason_codes = ("explicit-human-approval-required",)

    return ReleaseReview(
        review_id=review_id,
        stock_eligibility_decision_id=eligibility.decision_id,
        artifact_id=eligibility.artifact_id,
        evidence_id=eligibility.evidence_id,
        inspection_id=eligibility.inspection_id,
        quarantine_id=eligibility.quarantine_id,
        decision=decision,
        reviewed_at=reviewed_at,
        reviewed_by=reviewed_by,
        reason_codes=reason_codes,
        notes=notes,
    )
