"""Build bounded stock-release intents from approved human review records.

This module creates an authority-gated intent only. It does not register a
safety gate, executor, release handler, or inventory mutation path.
"""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.release_review import ReleaseReview, ReleaseReviewDecision
from business_agents.stock_eligibility import (
    StockEligibilityDecision,
    StockEligibilityStatus,
)


RELEASE_ROUTE = "inventory.stock-release"
RELEASE_ACTION = "prepare-bounded-release"


def build_release_intent(
    *,
    eligibility: StockEligibilityDecision,
    review: ReleaseReview,
    handler_id: str,
) -> BusinessIntent:
    validate_release_binding(eligibility=eligibility, review=review)
    if not isinstance(handler_id, str) or not handler_id.strip():
        raise ValueError("handler_id must be a non-empty string")

    return BusinessIntent(
        route=RELEASE_ROUTE,
        action=RELEASE_ACTION,
        subject_id=eligibility.evidence_id,
        parameters={
            "artifact_id": eligibility.artifact_id,
            "evidence_id": eligibility.evidence_id,
            "inspection_id": eligibility.inspection_id,
            "stock_eligibility_decision_id": eligibility.decision_id,
            "release_review_id": review.review_id,
            "handler_id": handler_id,
            "quarantine_id": eligibility.quarantine_id,
            "mutates_stock": False,
            "executes_release": False,
        },
        risk_level=RiskLevel.HIGH,
        approval_mode=ApprovalMode.STRONG_HUMAN,
    )


def validate_release_binding(
    *, eligibility: StockEligibilityDecision, review: ReleaseReview
) -> None:
    if eligibility.status is not StockEligibilityStatus.ELIGIBLE:
        raise ValueError("stock eligibility decision must be eligible")
    if eligibility.mutates_stock is not False:
        raise ValueError("stock eligibility decision must not mutate stock")
    if review.decision is not ReleaseReviewDecision.APPROVED:
        raise ValueError("release review must be approved")
    if review.mutates_stock is not False:
        raise ValueError("release review must not mutate stock")
    if review.executes_release is not False:
        raise ValueError("release review must not execute release")
    if review.stock_eligibility_decision_id != eligibility.decision_id:
        raise ValueError("release review decision binding mismatch")
    for name in ("artifact_id", "evidence_id", "inspection_id", "quarantine_id"):
        if getattr(review, name) != getattr(eligibility, name):
            raise ValueError(f"release review {name} binding mismatch")
