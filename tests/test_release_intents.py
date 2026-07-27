import pytest

from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.release_intents import RELEASE_ACTION, RELEASE_ROUTE, build_release_intent
from business_agents.release_package import ReleasePackage, build_release_package
from business_agents.release_review import ReleaseReview, ReleaseReviewDecision
from business_agents.stock_eligibility import StockEligibilityDecision, StockEligibilityStatus


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


def make_package(**changes):
    values = {
        "release_package_id": "release-package-001",
        "eligibility": make_eligibility(),
        "review": make_review(),
        "handler_id": "release-handler-v1",
    }
    values.update(changes)
    return build_release_package(**values)


def test_build_release_intent_from_immutable_package():
    package = make_package()
    intent = build_release_intent(package=package)
    assert intent.route == RELEASE_ROUTE
    assert intent.action == RELEASE_ACTION
    assert intent.subject_id == "release-package-001"
    assert intent.risk_level is RiskLevel.HIGH
    assert intent.approval_mode is ApprovalMode.STRONG_HUMAN
    assert intent.parameters["release_package_digest"] == package.package_digest
    assert intent.parameters["mutates_stock"] is False
    assert intent.parameters["executes_release"] is False


def test_release_intent_rejects_non_package():
    with pytest.raises(ValueError, match="ReleasePackage"):
        build_release_intent(package=object())


def test_release_package_rejects_tampered_digest():
    package = make_package()
    with pytest.raises(ValueError, match="does not match"):
        ReleasePackage(
            release_package_id=package.release_package_id,
            artifact_id=package.artifact_id,
            evidence_id=package.evidence_id,
            inspection_id=package.inspection_id,
            stock_eligibility_decision_id=package.stock_eligibility_decision_id,
            release_review_id=package.release_review_id,
            handler_id=package.handler_id,
            quarantine_id=package.quarantine_id,
            package_digest="f" * 64,
        )
