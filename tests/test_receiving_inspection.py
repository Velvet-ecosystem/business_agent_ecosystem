import pytest

from business_agents.receiving_inspection import (
    InspectionStatus,
    ReceivingInspection,
    ReceivingInspectionStore,
)


def make_inspection(**changes):
    values = {
        "inspection_id": "insp-001",
        "evidence_id": "recv-001",
        "artifact_id": "artifact-001",
        "status": InspectionStatus.MATCHED,
        "quantity_expected": 2,
        "quantity_received": 2,
        "supplier_part_expected": "SUP-001",
        "supplier_part_received": "SUP-001",
        "manufacturer_part_expected": "MPN-001",
        "manufacturer_part_received": "MPN-001",
        "inspected_at": "2026-07-16T02:45:00+00:00",
        "inspected_by": "Mister",
        "findings": (),
    }
    values.update(changes)
    return ReceivingInspection(**values)


def test_receiving_inspection_round_trip(tmp_path):
    store = ReceivingInspectionStore(tmp_path / "inspections.jsonl")
    inspection = make_inspection()

    store.add(inspection)
    stored = store.get("insp-001")

    assert stored == inspection
    assert stored is not None
    assert stored.eligible_for_stock is False
    assert stored.payload()["eligible_for_stock"] is False
    assert stored.payload()["status"] == "matched"


def test_receiving_inspection_lists_by_evidence(tmp_path):
    store = ReceivingInspectionStore(tmp_path / "inspections.jsonl")
    first = make_inspection(inspection_id="insp-001", evidence_id="recv-001")
    second = make_inspection(inspection_id="insp-002", evidence_id="recv-002")

    store.add(first)
    store.add(second)

    assert store.list_for_evidence("recv-001") == (first,)
    assert store.list_for_evidence("recv-002") == (second,)


def test_duplicate_inspection_id_is_rejected(tmp_path):
    store = ReceivingInspectionStore(tmp_path / "inspections.jsonl")
    inspection = make_inspection()
    store.add(inspection)

    with pytest.raises(ValueError):
        store.add(inspection)


def test_non_matched_inspection_requires_findings():
    with pytest.raises(ValueError, match="findings"):
        make_inspection(status=InspectionStatus.NEEDS_REVIEW, findings=())


def test_matched_inspection_rejects_findings():
    with pytest.raises(ValueError, match="matched"):
        make_inspection(status=InspectionStatus.MATCHED, findings=("Unexpected mark.",))


def test_rejected_inspection_round_trip_with_findings(tmp_path):
    store = ReceivingInspectionStore(tmp_path / "inspections.jsonl")
    inspection = make_inspection(
        status=InspectionStatus.REJECTED,
        quantity_received=1,
        supplier_part_received="SUP-WRONG",
        findings=("quantity-mismatch", "supplier-part-mismatch"),
    )

    store.add(inspection)
    stored = store.get("insp-001")

    assert stored == inspection
    assert stored.status is InspectionStatus.REJECTED
    assert stored.findings == ("quantity-mismatch", "supplier-part-mismatch")
    assert stored.eligible_for_stock is False


def test_receiving_inspection_rejects_invalid_quantity():
    with pytest.raises(ValueError, match="positive"):
        make_inspection(quantity_expected=0)
    with pytest.raises(ValueError, match="integer"):
        make_inspection(quantity_received=True)


def test_receiving_inspection_rejects_empty_required_fields():
    with pytest.raises(ValueError, match="artifact_id"):
        make_inspection(artifact_id="")
    with pytest.raises(ValueError, match="inspected_by"):
        make_inspection(inspected_by=" ")
