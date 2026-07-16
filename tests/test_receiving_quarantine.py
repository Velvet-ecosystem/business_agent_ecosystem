import pytest

from business_agents.receiving_quarantine import (
    QuarantineStatus,
    ReceivingQuarantine,
    ReceivingQuarantineStore,
)


def make_quarantine(**changes):
    values = {
        "quarantine_id": "q-001",
        "inspection_id": "insp-001",
        "evidence_id": "recv-001",
        "artifact_id": "artifact-001",
        "status": QuarantineStatus.HELD_FOR_REVIEW,
        "reason_codes": ("quantity-mismatch",),
        "held_at": "2026-07-16T03:45:00+00:00",
        "held_by": "Mister",
        "notes": ("Hold until reviewed.",),
    }
    values.update(changes)
    return ReceivingQuarantine(**values)


def test_receiving_quarantine_round_trip(tmp_path):
    store = ReceivingQuarantineStore(tmp_path / "quarantine.jsonl")
    quarantine = make_quarantine()

    store.add(quarantine)
    stored = store.get("q-001")

    assert stored == quarantine
    assert stored is not None
    assert stored.eligible_for_stock is False
    assert stored.payload()["eligible_for_stock"] is False
    assert stored.payload()["status"] == "held-for-review"
    assert stored.payload()["reason_codes"] == ["quantity-mismatch"]


def test_receiving_quarantine_lists_by_inspection(tmp_path):
    store = ReceivingQuarantineStore(tmp_path / "quarantine.jsonl")
    first = make_quarantine(quarantine_id="q-001", inspection_id="insp-001")
    second = make_quarantine(quarantine_id="q-002", inspection_id="insp-002")

    store.add(first)
    store.add(second)

    assert store.list_for_inspection("insp-001") == (first,)
    assert store.list_for_inspection("insp-002") == (second,)


def test_duplicate_quarantine_id_is_rejected(tmp_path):
    store = ReceivingQuarantineStore(tmp_path / "quarantine.jsonl")
    quarantine = make_quarantine()
    store.add(quarantine)

    with pytest.raises(ValueError):
        store.add(quarantine)


def test_rejected_quarantine_round_trip(tmp_path):
    store = ReceivingQuarantineStore(tmp_path / "quarantine.jsonl")
    quarantine = make_quarantine(
        status=QuarantineStatus.REJECTED,
        reason_codes=("supplier-part-mismatch", "damaged-package"),
        notes=("Wrong part and damaged box.",),
    )

    store.add(quarantine)
    stored = store.get("q-001")

    assert stored == quarantine
    assert stored.status is QuarantineStatus.REJECTED
    assert stored.reason_codes == ("supplier-part-mismatch", "damaged-package")
    assert stored.eligible_for_stock is False


def test_release_review_required_still_not_stock_eligible():
    quarantine = make_quarantine(
        status=QuarantineStatus.RELEASE_REVIEW_REQUIRED,
        reason_codes=("resolved-by-human-review",),
        notes=("Needs a separate future release gate.",),
    )

    assert quarantine.eligible_for_stock is False
    assert quarantine.payload()["eligible_for_stock"] is False


def test_quarantine_requires_reason_codes():
    with pytest.raises(ValueError, match="reason_codes"):
        make_quarantine(reason_codes=())
    with pytest.raises(ValueError, match="reason_codes"):
        make_quarantine(reason_codes=("",))


def test_quarantine_rejects_empty_required_fields():
    with pytest.raises(ValueError, match="inspection_id"):
        make_quarantine(inspection_id="")
    with pytest.raises(ValueError, match="held_by"):
        make_quarantine(held_by=" ")


def test_quarantine_rejects_empty_notes():
    with pytest.raises(ValueError, match="notes"):
        make_quarantine(notes=("",))
