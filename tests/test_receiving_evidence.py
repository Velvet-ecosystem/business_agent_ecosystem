import pytest

from business_agents.receiving_evidence import ReceivingEvidence, ReceivingEvidenceStore


def make_evidence(**changes):
    values = {
        "evidence_id": "recv-001",
        "artifact_id": "artifact-001",
        "received_reference": "package-001",
        "carrier_reference": "carrier-001",
        "package_condition": "sealed",
        "claimed_supplier_name": "Supplier One",
        "claimed_supplier_part_number": "SUP-001",
        "claimed_manufacturer_part_number": "MPN-001",
        "quantity_received": 2,
        "received_at": "2026-07-16T02:30:00+00:00",
        "received_by": "Mister",
        "notes": ("Box intact.",),
    }
    values.update(changes)
    return ReceivingEvidence(**values)


def test_receiving_evidence_round_trip(tmp_path):
    store = ReceivingEvidenceStore(tmp_path / "receiving.jsonl")
    evidence = make_evidence()

    store.add(evidence)
    stored = store.get("recv-001")

    assert stored == evidence
    assert stored is not None
    assert stored.payload()["notes"] == ["Box intact."]


def test_receiving_evidence_lists_by_artifact(tmp_path):
    store = ReceivingEvidenceStore(tmp_path / "receiving.jsonl")
    first = make_evidence(evidence_id="recv-001", artifact_id="artifact-001")
    second = make_evidence(evidence_id="recv-002", artifact_id="artifact-002")

    store.add(first)
    store.add(second)

    assert store.list_for_artifact("artifact-001") == (first,)
    assert store.list_for_artifact("artifact-002") == (second,)


def test_duplicate_evidence_id_is_rejected(tmp_path):
    store = ReceivingEvidenceStore(tmp_path / "receiving.jsonl")
    evidence = make_evidence()
    store.add(evidence)

    with pytest.raises(ValueError):
        store.add(evidence)


def test_receiving_evidence_rejects_invalid_quantity():
    with pytest.raises(ValueError, match="positive"):
        make_evidence(quantity_received=0)
    with pytest.raises(ValueError, match="integer"):
        make_evidence(quantity_received=True)


def test_receiving_evidence_rejects_empty_required_fields():
    with pytest.raises(ValueError, match="artifact_id"):
        make_evidence(artifact_id="")
    with pytest.raises(ValueError, match="received_by"):
        make_evidence(received_by=" ")


def test_receiving_evidence_rejects_empty_notes():
    with pytest.raises(ValueError, match="notes"):
        make_evidence(notes=("",))
