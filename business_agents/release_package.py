"""Immutable release packages for exact authority binding."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.release_review import ReleaseReview, ReleaseReviewDecision
from business_agents.stock_eligibility import (
    StockEligibilityDecision,
    StockEligibilityStatus,
)


@dataclass(frozen=True)
class ReleasePackage:
    release_package_id: str
    artifact_id: str
    evidence_id: str
    inspection_id: str
    stock_eligibility_decision_id: str
    release_review_id: str
    handler_id: str
    quarantine_id: str | None
    package_digest: str

    def __post_init__(self) -> None:
        for name in (
            "release_package_id",
            "artifact_id",
            "evidence_id",
            "inspection_id",
            "stock_eligibility_decision_id",
            "release_review_id",
            "handler_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.quarantine_id is not None and (
            not isinstance(self.quarantine_id, str) or not self.quarantine_id.strip()
        ):
            raise ValueError("quarantine_id must be None or a non-empty string")
        if len(self.package_digest) != 64 or any(
            character not in "0123456789abcdef" for character in self.package_digest
        ):
            raise ValueError("package_digest must be a lowercase SHA-256 hex digest")
        if self.package_digest != calculate_release_package_digest(self.canonical_payload()):
            raise ValueError("package_digest does not match canonical release package")

    @property
    def mutates_stock(self) -> bool:
        return False

    @property
    def executes_release(self) -> bool:
        return False

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "evidence_id": self.evidence_id,
            "handler_id": self.handler_id,
            "inspection_id": self.inspection_id,
            "quarantine_id": self.quarantine_id,
            "release_package_id": self.release_package_id,
            "release_review_id": self.release_review_id,
            "stock_eligibility_decision_id": self.stock_eligibility_decision_id,
        }

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["mutates_stock"] = self.mutates_stock
        data["executes_release"] = self.executes_release
        return data


class ReleasePackageStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._storage = CompatibleLockedJsonlFile(
            self.path, schema="release-package", version=1
        )

    def add(self, package: ReleasePackage) -> ReleasePackage:
        self._storage.append_unique(package.payload(), field="release_package_id")
        return package

    def get(self, release_package_id: str) -> ReleasePackage | None:
        if not isinstance(release_package_id, str) or not release_package_id.strip():
            raise ValueError("release_package_id must be a non-empty string")
        for data in reversed(self._storage.read_all()):
            if data.get("release_package_id") == release_package_id:
                return self._from_payload(data)
        return None

    @staticmethod
    def _from_payload(data: Mapping[str, Any]) -> ReleasePackage:
        payload = dict(data)
        payload.pop("mutates_stock", None)
        payload.pop("executes_release", None)
        return ReleasePackage(**payload)


def build_release_package(
    *,
    release_package_id: str,
    eligibility: StockEligibilityDecision,
    review: ReleaseReview,
    handler_id: str,
) -> ReleasePackage:
    if eligibility.status is not StockEligibilityStatus.ELIGIBLE:
        raise ValueError("stock eligibility decision must be eligible")
    if review.decision is not ReleaseReviewDecision.APPROVED:
        raise ValueError("release review must be approved")
    if review.stock_eligibility_decision_id != eligibility.decision_id:
        raise ValueError("release review decision binding mismatch")
    for name in ("artifact_id", "evidence_id", "inspection_id", "quarantine_id"):
        if getattr(review, name) != getattr(eligibility, name):
            raise ValueError(f"release review {name} binding mismatch")
    if not isinstance(release_package_id, str) or not release_package_id.strip():
        raise ValueError("release_package_id must be a non-empty string")
    if not isinstance(handler_id, str) or not handler_id.strip():
        raise ValueError("handler_id must be a non-empty string")

    canonical = {
        "artifact_id": eligibility.artifact_id,
        "evidence_id": eligibility.evidence_id,
        "handler_id": handler_id,
        "inspection_id": eligibility.inspection_id,
        "quarantine_id": eligibility.quarantine_id,
        "release_package_id": release_package_id,
        "release_review_id": review.review_id,
        "stock_eligibility_decision_id": eligibility.decision_id,
    }
    return ReleasePackage(
        release_package_id=release_package_id,
        artifact_id=eligibility.artifact_id,
        evidence_id=eligibility.evidence_id,
        inspection_id=eligibility.inspection_id,
        stock_eligibility_decision_id=eligibility.decision_id,
        release_review_id=review.review_id,
        handler_id=handler_id,
        quarantine_id=eligibility.quarantine_id,
        package_digest=calculate_release_package_digest(canonical),
    )


def calculate_release_package_digest(payload: Mapping[str, Any]) -> str:
    canonical_json = json.dumps(
        dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
