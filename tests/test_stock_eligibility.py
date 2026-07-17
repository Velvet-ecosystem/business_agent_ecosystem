import pytest

from business_agents.receiving_verification import ReceivingVerification
from business_agents.stock_eligibility import (
    StockEligibilityDecision,
    StockEligibilityStatus,
    StockEligibilityStore,
    propose_stock_eligibility_decision,
)


def make_decision(**changes):
    values = {
        "decision_id": "stock-001",
        "verification_reason": "verified-matched-receiving-chain",
        "artifact_id": "artifact-001",
        "evidence_id": "recv-001",
        "inspection_id": "insp-001",
        "status": StockEligibilityStatus.ELIGIBLE,
        "decided_at": "2026-07-16T05:45:00+00:00",
        "decided_by": "Mister",
        "reason_codes": ("verified-matched-receiving-chain",),
        "quarantine_id": None,
        "notes": (),
    }
    values.update(changes)
    return StockEligibilityDecision(**values)


def test_stock_eligibility_round_trip(tmp_path):
    store = StockEligibilityStore(tmp_path / "stock_eligibility.jsonl")
    decision = make_decision()

    store.add(decision)
    stored = store.get("stock-001")

    assert stored == decision
    assert stored is not None
    assert stored.mutates_stock is False
    assert stored.payload()["mutates_stock"] is False
    assert stored.payload()["status"] == "eligible"


def test_stock_eligibility_lists_by_evidence(tmp_path):
    store = StockEligibilityStore(tmp_path / "stock_eligibility.jsonl")
    first = make_decision(decision_id="stock-001", evidence_id="recv-001")
    second = make_decision(decision_id="stock-002", evidence_id="recv-002")

    store.add(first)
    store.add(second)

    assert store.list_for_evidence("recv-001") == (first,)
    assert store.list_for_evidence("recv-002") == (second,)


def test_duplicate_stock_eligibility_decision_is_rejected(tmp_path):
    store = StockEligibilityStore(tmp_path / "stock_eligibility.jsonl")
    decision = make_decision()
    store.add(decision)

    with pytest.raises(ValueError):
        store.add(decision)


def test_propose_eligible_for_matched_verified_chain():
    decision = propose_stock_eligibility_decision(
        decision_id="stock-001",
        verification=ReceivingVerification(True, "verified-matched-receiving-chain"),
        artifact_id="artifact-001",
        evidence_id="recv-001",
        inspection_id="insp-001",
        decided_at="2026-07-16T05:45:00+00:00",
        decided_by="Mister",
    )

    assert decision.status is StockEligibilityStatus.ELIGIBLE
    assert decision.reason_codes == ("verified-matched-receiving-chain",)
    assert decision.mutates_stock is False


def test_propose_review_required_for_quarantined_verified_chain():
    decision = propose_stock_eligibility_decision(
        decision_id="stock-001",
        verification=ReceivingVerification(True, "verified-quarantined-receiving-chain"),
        artifact_id="artifact-001",
        evidence_id="recv-001",
        inspection_id="insp-001",
        quarantine_id="q-001",
        decided_at="2026-07-16T05:45:00+00:00",
        decided_by="Mister",
    )

    assert decision.status is StockEligibilityStatus.REVIEW_REQUIRED
    assert decision.reason_codes == ("verified-quarantined-receiving-chain",)
    assert decision.quarantine_id == "q-001"
    assert decision.mutates_stock is False


def test_propose_not_eligible_for_failed_receiving_verification():
    decision = propose_stock_eligibility_decision(
        decision_id="stock-001",
        verification=ReceivingVerification(False, "inspection-quantity-mismatch"),
        artifact_id="artifact-001",
        evidence_id="recv-001",
        inspection_id="insp-001",
        decided_at="2026-07-16T05:45:00+00:00",
        decided_by="Mister",
    )

    assert decision.status is StockEligibilityStatus.NOT_ELIGIBLE
    assert decision.reason_codes == ("inspection-quantity-mismatch",)
    assert decision.mutates_stock is False


def test_stock_eligibility_rejects_empty_required_fields():
    with pytest.raises(ValueError, match="artifact_id"):
        make_decision(artifact_id="")
    with pytest.raises(ValueError, match="decided_by"):
        make_decision(decided_by=" ")


def test_stock_eligibility_requires_reason_codes():
    with pytest.raises(ValueError, match="reason_codes"):
        make_decision(reason_codes=())
    with pytest.raises(ValueError, match="reason_codes"):
        make_decision(reason_codes=("",))


def test_stock_eligibility_rejects_empty_quarantine_id():
    with pytest.raises(ValueError, match="quarantine_id"):
        make_decision(quarantine_id="")
