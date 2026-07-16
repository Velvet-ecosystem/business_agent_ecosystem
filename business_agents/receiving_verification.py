"""Read-only verification for receiving evidence chains."""

from __future__ import annotations

from dataclasses import dataclass

from business_agents.receiving_evidence import ReceivingEvidence
from business_agents.receiving_inspection import InspectionStatus, ReceivingInspection
from business_agents.receiving_quarantine import ReceivingQuarantine


@dataclass(frozen=True)
class ReceivingVerification:
    passed: bool
    reason: str


def verify_receiving_chain(
    *,
    evidence: ReceivingEvidence,
    inspection: ReceivingInspection,
    quarantine: ReceivingQuarantine | None = None,
) -> ReceivingVerification:
    if inspection.evidence_id != evidence.evidence_id:
        return ReceivingVerification(False, "inspection-evidence-mismatch")
    if inspection.artifact_id != evidence.artifact_id:
        return ReceivingVerification(False, "inspection-artifact-mismatch")
    if inspection.quantity_received != evidence.quantity_received:
        return ReceivingVerification(False, "inspection-quantity-mismatch")
    if inspection.supplier_part_received != evidence.claimed_supplier_part_number:
        return ReceivingVerification(False, "inspection-supplier-part-mismatch")
    if (
        inspection.manufacturer_part_received
        != evidence.claimed_manufacturer_part_number
    ):
        return ReceivingVerification(False, "inspection-manufacturer-part-mismatch")
    if inspection.eligible_for_stock is not False:
        return ReceivingVerification(False, "inspection-stock-eligible")

    if inspection.status is InspectionStatus.MATCHED:
        if quarantine is not None:
            return ReceivingVerification(False, "matched-inspection-has-quarantine")
        return ReceivingVerification(True, "verified-matched-receiving-chain")

    if quarantine is None:
        return ReceivingVerification(False, "non-matched-inspection-missing-quarantine")
    if quarantine.inspection_id != inspection.inspection_id:
        return ReceivingVerification(False, "quarantine-inspection-mismatch")
    if quarantine.evidence_id != evidence.evidence_id:
        return ReceivingVerification(False, "quarantine-evidence-mismatch")
    if quarantine.artifact_id != evidence.artifact_id:
        return ReceivingVerification(False, "quarantine-artifact-mismatch")
    if quarantine.eligible_for_stock is not False:
        return ReceivingVerification(False, "quarantine-stock-eligible")
    if not set(inspection.findings).issubset(set(quarantine.reason_codes)):
        return ReceivingVerification(False, "quarantine-missing-inspection-findings")
    return ReceivingVerification(True, "verified-quarantined-receiving-chain")
