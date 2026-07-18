import pytest

from business_agents.release_review import (
    ReleaseReview,
    ReleaseReviewDecision,
    ReleaseReviewStore,
    propose_release_review,
)
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
        "decided_at": "2026-07-18T10:00:00+00:00",
        "decided_by": "Mister",
        "reason_codes": ("verified-matched-receiving-chain",),
        "quarantine_id": None,
        "notes": (),
    }
    values.update(changes)
    return StockEligibilityDecision(**values)


def make_review(**changes):
    values = {
        "review_id": "release-001",
        "stock_eligibility_decision_id": "stock-001",
        "artifact_id": "artifact-001",
        "evidence_id": "recv-001",
        "inspection_id": "insp-001",
        "decision": ReleaseReviewDecision.APPROVED,
        "reviewed_at": "2026-07-18T10:05:00+00:00",
        "reviewed_by": "Mister",
        "reason_codes": ("human-approved-eligible-record",),
        "quarantine_id": None,
        "notes": (),
    }
    values.update(changes)
    return ReleaseReview(**values)


def test_release_review_round_trip(tmp_path):
    store = ReleaseReviewStore(tmp_path / "release_reviews.jsonl")
    review = make_review()

    store.add(review)
    stored = store.get("release-001")

    assert stored == review
    assert stored is not None
    assert stored.mutates_stock is False
    assert stored.executes_release is False
    assert stored.payload()["mutates_stock"] is False
    assert stored.payload()["executes_release"] is False


def test_release_review_lists_by_eligibility_decision(tmp_path):
    store = ReleaseReviewStore(tmp_path / "release_reviews.jsonl")
    first = make_review(review_id="release-001", stock_eligibility_decision_id="stock-001")
    second = make_review(review_id="release-002", stock_eligibility_decision_id="stock-002")

    store.add(first)
    store.add(second)

    assert store.list_for_eligibility_decision("stock-001") == (first,)
    assert store.list_for_eligibility_decision("stock-002") == (second,)


def test_duplicate_release_review_is_rejected(tmp_path):
    store = ReleaseReviewStore(tmp_path / "release_reviews.jsonl")
    review = make_review()
    store.add(review)

    with pytest.raises(ValueError):
        store.add(review)


def test_eligible_record_requires_explicit_human_approval():
    review = propose_release_review(
        review_id="release-001",
        eligibility=make_eligibility(),
        reviewed_at="2026-07-18T10:05:00+00:00",
        reviewed_by="Mister",
    )

    assert review.decision is ReleaseReviewDecision.NEEDS_MORE_EVIDENCE
    assert review.reason_codes == ("explicit-human-approval-required",)
    assert review.executes_release is False


def test_eligible_record_can_be_approved_as_a_record_only():
    review = propose_release_review(
        review_id="release-001",
        eligibility=make_eligibility(),
        reviewed_at="2026-07-18T10:05:00+00:00",
        reviewed_by="Mister",
        approve_eligible=True,
    )

    assert review.decision is ReleaseReviewDecision.APPROVED
    assert review.reason_codes == ("human-approved-eligible-record",)
    assert review.mutates_stock is False
    assert review.executes_release is False


def test_not_eligible_record_is_denied():
    review = propose_release_review(
        review_id="release-001",
        eligibility=make_eligibility(status=StockEligibilityStatus.NOT_ELIGIBLE),
        reviewed_at="2026-07-18T10:05:00+00:00",
        reviewed_by="Mister",
        approve_eligible=True,
    )

    assert review.decision is ReleaseReviewDecision.DENIED
    assert review.reason_codes == ("stock-not-eligible",)


def test_review_required_record_needs_more_evidence():
    review = propose_release_review(
        review_id="release-001",
        eligibility=make_eligibility(
            status=StockEligibilityStatus.REVIEW_REQUIRED,
            quarantine_id="q-001",
        ),
        reviewed_at="2026-07-18T10:05:00+00:00",
        reviewed_by="Mister",
        approve_eligible=True,
    )

    assert review.decision is ReleaseReviewDecision.NEEDS_MORE_EVIDENCE
    assert review.reason_codes == ("stock-review-required",)
    assert review.quarantine_id == "q-001"


def test_release_review_rejects_empty_required_fields():
    with pytest.raises(ValueError, match="artifact_id"):
        make_review(artifact_id="")
    with pytest.raises(ValueError, match="reviewed_by"):
        make_review(reviewed_by=" ")


def test_release_review_requires_reason_codes():
    with pytest.raises(ValueError, match="reason_codes"):
        make_review(reason_codes=())
    with pytest.raises(ValueError, match="reason_codes"):
        make_review(reason_codes=("",))
