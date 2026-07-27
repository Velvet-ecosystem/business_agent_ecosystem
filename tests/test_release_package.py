import pytest

from business_agents.release_package import ReleasePackage, ReleasePackageStore, build_release_package
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


def test_release_package_digest_is_deterministic():
    first = make_package()
    second = make_package()
    assert first.package_digest == second.package_digest
    assert len(first.package_digest) == 64
    assert first.mutates_stock is False
    assert first.executes_release is False


def test_release_package_round_trip(tmp_path):
    store = ReleasePackageStore(tmp_path / "release_packages.jsonl")
    package = make_package()
    store.add(package)
    assert store.get("release-package-001") == package


def test_duplicate_release_package_id_is_rejected(tmp_path):
    store = ReleasePackageStore(tmp_path / "release_packages.jsonl")
    package = make_package()
    store.add(package)
    with pytest.raises(ValueError):
        store.add(package)


def test_release_package_rejects_changed_digest():
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
            package_digest="0" * 64,
        )


def test_release_package_rejects_non_eligible_decision():
    with pytest.raises(ValueError, match="must be eligible"):
        make_package(eligibility=make_eligibility(status=StockEligibilityStatus.NOT_ELIGIBLE))


def test_release_package_rejects_non_approved_review():
    with pytest.raises(ValueError, match="must be approved"):
        make_package(review=make_review(decision=ReleaseReviewDecision.DENIED))


def test_release_package_rejects_binding_mismatch():
    with pytest.raises(ValueError, match="evidence_id binding mismatch"):
        make_package(review=make_review(evidence_id="recv-002"))


def test_release_package_rejects_empty_handler_id():
    with pytest.raises(ValueError, match="handler_id"):
        make_package(handler_id=" ")
