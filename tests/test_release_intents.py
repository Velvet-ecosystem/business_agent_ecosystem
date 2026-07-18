import pytest

from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.release_intents import (
    RELEASE_ACTION,
    RELEASE_ROUTE,
    build_release_intent,
)
from business_agents.release_review import ReleaseReview, ReleaseReviewDecision
from business_agents.stock_eligibility import (
    StockEligibilityDecision,
    StockEligibilityStatus,
)


def make_eligibility(**changes):
    values = {
        "decision_id": "stock-001",
        "verification_reason": "verified-matched-receiving-chain",
        "artifact_id": "artifact-001",
        "evidence_id": "recv-001",
        "inspection_id": "insp-001",
        "status": StockEligibilityStatus.ELIGIBLE,
        "decided_at": "2026-07-18T21:30:00+00:00",
        "decided_by": "Mister",
        "reason_codes": ("verified-matched-receiving-chain",),
        "quarantine_id": None,
        "notes": (),
    }
    values.update(changes)
    return StockEligibilityDecision(**values)


def make_review(**changes):
    values = {
        "review_id": "review-001",
        "stock_eligibility_decision_id": "stock-001",
        "artifact_id": "artifact-001",
        "evidence_id": "recv-001",
        "inspection_id": "insp-001",
        "decision": ReleaseReviewDecision.APPROVED,
        "reviewed_at": "2026-07-18T21:35:00+00:00",
        "reviewed_by": "Mister",
        "reason_codes": ("human-approved-eligible-record",),
        "quarantine_id": None,
        "notes": (),
    }
    values.update(changes)
    return ReleaseReview(**values)


def test_build_release_intent_from_exact_approved_binding():
    intent = build_release_intent(
        eligibility=make_eligibility(),
        review=make_review(),
        handler_id="release-handler-v1",
    )

    assert intent.route == RELEASE_ROUTE
    assert intent.action == RELEASE_ACTION
    assert intent.subject_id == "recv-001"
    assert intent.risk_level is RiskLevel.HIGH
    assert intent.approval_mode is ApprovalMode.STRONG_HUMAN
    assert intent.parameters["stock_eligibility_decision_id"] == "stock-001"
    assert intent.parameters["release_review_id"] == "review-001"
    assert intent.parameters["mutates_stock"] is False
    assert intent.parameters["executes_release"] is False


def test_release_intent_rejects_non_eligible_decision():
    with pytest.raises(ValueError, match="must be eligible"):
        build_release_intent(
            eligibility=make_eligibility(status=StockEligibilityStatus.NOT_ELIGIBLE),
            review=make_review(),
            handler_id="release-handler-v1",
        )


def test_release_intent_rejects_non_approved_review():
    with pytest.raises(ValueError, match="must be approved"):
        build_release_intent(
            eligibility=make_eligibility(),
            review=make_review(decision=ReleaseReviewDecision.DENIED),
            handler_id="release-handler-v1",
        )


def test_release_intent_rejects_decision_binding_mismatch():
    with pytest.raises(ValueError, match="decision binding mismatch"):
        build_release_intent(
            eligibility=make_eligibility(),
            review=make_review(stock_eligibility_decision_id="stock-002"),
            handler_id="release-handler-v1",
        )


def test_release_intent_rejects_evidence_binding_mismatch():
    with pytest.raises(ValueError, match="evidence_id binding mismatch"):
        build_release_intent(
            eligibility=make_eligibility(),
            review=make_review(evidence_id="recv-002"),
            handler_id="release-handler-v1",
        )


def test_release_intent_rejects_empty_handler_id():
    with pytest.raises(ValueError, match="handler_id"):
        build_release_intent(
            eligibility=make_eligibility(),
            review=make_review(),
            handler_id=" ",
        )
