"""Build bounded stock-release intents from immutable release packages.

This module creates an authority-gated intent only. It does not register a
safety gate, executor, release handler, or inventory mutation path.
"""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.release_package import ReleasePackage


RELEASE_ROUTE = "inventory.stock-release"
RELEASE_ACTION = "prepare-bounded-release"


def build_release_intent(*, package: ReleasePackage) -> BusinessIntent:
    validate_release_package(package)

    return BusinessIntent(
        route=RELEASE_ROUTE,
        action=RELEASE_ACTION,
        subject_id=package.release_package_id,
        parameters={
            "release_package_id": package.release_package_id,
            "release_package_digest": package.package_digest,
            "artifact_id": package.artifact_id,
            "evidence_id": package.evidence_id,
            "inspection_id": package.inspection_id,
            "stock_eligibility_decision_id": package.stock_eligibility_decision_id,
            "release_review_id": package.release_review_id,
            "handler_id": package.handler_id,
            "quarantine_id": package.quarantine_id,
            "mutates_stock": False,
            "executes_release": False,
        },
        risk_level=RiskLevel.HIGH,
        approval_mode=ApprovalMode.STRONG_HUMAN,
    )


def validate_release_package(package: ReleasePackage) -> None:
    if not isinstance(package, ReleasePackage):
        raise ValueError("package must be a ReleasePackage")
    if package.mutates_stock is not False:
        raise ValueError("release package must not mutate stock")
    if package.executes_release is not False:
        raise ValueError("release package must not execute release")
