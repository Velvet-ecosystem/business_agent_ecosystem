from business_agents.receiving_evidence import ReceivingEvidence
from business_agents.receiving_inspection import InspectionStatus, ReceivingInspection
from business_agents.receiving_quarantine import QuarantineStatus, ReceivingQuarantine
from business_agents.receiving_verification import verify_receiving_chain


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
        "received_at": "2026-07-16T04:20:00+00:00",
        "received_by": "Mister",
        "notes": (),
    }
    values.update(changes)
    return ReceivingEvidence(**values)


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
        "inspected_at": "2026-07-16T04:25:00+00:00",
        "inspected_by": "Mister",
        "findings": (),
    }
    values.update(changes)
    return ReceivingInspection(**values)


def make_quarantine(**changes):
    values = {
        "quarantine_id": "q-001",
        "inspection_id": "insp-001",
        "evidence_id": "recv-001",
        "artifact_id": "artifact-001",
        "status": QuarantineStatus.HELD_FOR_REVIEW,
        "reason_codes": ("quantity-mismatch",),
        "held_at": "2026-07-16T04:30:00+00:00",
        "held_by": "Mister",
        "notes": (),
    }
    values.update(changes)
    return ReceivingQuarantine(**values)


def test_verifier_accepts_matched_chain_without_quarantine():
    result = verify_receiving_chain(
        evidence=make_evidence(),
        inspection=make_inspection(),
    )

    assert result.passed is True
    assert result.reason == "verified-matched-receiving-chain"


def test_verifier_rejects_matched_chain_with_quarantine():
    result = verify_receiving_chain(
        evidence=make_evidence(),
        inspection=make_inspection(),
        quarantine=make_quarantine(reason_codes=("manual-hold",)),
    )

    assert result.passed is False
    assert result.reason == "matched-inspection-has-quarantine"


def test_verifier_accepts_non_matched_chain_with_quarantine():
    inspection = make_inspection(
        status=InspectionStatus.NEEDS_REVIEW,
        quantity_received=1,
        findings=("quantity-mismatch",),
    )
    evidence = make_evidence(quantity_received=1)
    quarantine = make_quarantine(reason_codes=("quantity-mismatch",))

    result = verify_receiving_chain(
        evidence=evidence,
        inspection=inspection,
        quarantine=quarantine,
    )

    assert result.passed is True
    assert result.reason == "verified-quarantined-receiving-chain"


def test_verifier_rejects_non_matched_chain_without_quarantine():
    inspection = make_inspection(
        status=InspectionStatus.REJECTED,
        supplier_part_received="SUP-WRONG",
        findings=("supplier-part-mismatch",),
    )
    evidence = make_evidence(claimed_supplier_part_number="SUP-WRONG")

    result = verify_receiving_chain(evidence=evidence, inspection=inspection)

    assert result.passed is False
    assert result.reason == "non-matched-inspection-missing-quarantine"


def test_verifier_rejects_inspection_evidence_mismatch():
    result = verify_receiving_chain(
        evidence=make_evidence(evidence_id="recv-001"),
        inspection=make_inspection(evidence_id="recv-002"),
    )

    assert result.passed is False
    assert result.reason == "inspection-evidence-mismatch"


def test_verifier_rejects_inspection_quantity_mismatch():
    result = verify_receiving_chain(
        evidence=make_evidence(quantity_received=2),
        inspection=make_inspection(quantity_received=1),
    )

    assert result.passed is False
    assert result.reason == "inspection-quantity-mismatch"


def test_verifier_rejects_quarantine_missing_inspection_findings():
    inspection = make_inspection(
        status=InspectionStatus.REJECTED,
        supplier_part_received="SUP-WRONG",
        findings=("supplier-part-mismatch",),
    )
    evidence = make_evidence(claimed_supplier_part_number="SUP-WRONG")
    quarantine = make_quarantine(reason_codes=("manual-hold",))

    result = verify_receiving_chain(
        evidence=evidence,
        inspection=inspection,
        quarantine=quarantine,
    )

    assert result.passed is False
    assert result.reason == "quarantine-missing-inspection-findings"
