from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.approval_requests import ApprovalRequestStore
from business_agents.procurement import SupplierCandidate, SupplierCandidateStore
from business_agents.procurement_requirements import ProcurementRequirement, ProcurementRequirementStore
from business_agents.skills.queue_purchase_request import QueuePurchaseRequestSkill


def _build_skill(tmp_path: Path) -> tuple[QueuePurchaseRequestSkill, ApprovalRequestStore, Path]:
    requirements = ProcurementRequirementStore(tmp_path / "requirements.jsonl")
    candidates = SupplierCandidateStore(tmp_path / "candidates.jsonl")
    approval_path = tmp_path / "approvals.jsonl"
    approvals = ApprovalRequestStore(approval_path)
    requirements.create(
        ProcurementRequirement(
            requirement_id="req-001",
            item_name="Automotive relay",
            quantity=2,
            intended_use="Isolated accessory control",
            compatibility_constraints=("12V coil", "automotive-rated"),
            acceptable_substitutions=("sealed equivalent",),
            target_budget=Decimal("40.00"),
            currency="CAD",
            required_evidence=("datasheet", "pinout"),
            urgency="normal",
            source_reference="job://job-001",
        )
    )
    candidates.create(
        SupplierCandidate(
            candidate_id="cand-001",
            requirement_id="req-001",
            supplier_name="Supplier One",
            supplier_part_number="SUP-001",
            manufacturer_part_number="MPN-001",
            quantity=2,
            unit_price=Decimal("15.00"),
            shipping_cost=Decimal("5.00"),
            currency="CAD",
            source_reference="source://candidate-001",
            compatibility_evidence=("datasheet-pinout-match",),
        )
    )
    return QueuePurchaseRequestSkill(requirements, candidates, approvals), approvals, approval_path


def test_queue_purchase_request_creates_pending_review_without_authority(tmp_path: Path) -> None:
    skill, approvals, approval_path = _build_skill(tmp_path)

    result = skill.run(
        {
            "approval_request_id": "approval-001",
            "requirement_id": "req-001",
            "candidate_id": "cand-001",
            "requested_by": "procurement-agent",
        }
    )

    assert result.output["approval_request"] == {
        "request_id": "approval-001",
        "route": "procurement.order",
        "action": "place-bounded-order",
        "subject_id": "req-001",
        "summary": "Review purchase of 2 x Automotive relay from Supplier One for 35.00 CAD",
        "risk_level": "high",
        "approval_mode": "strong-human",
        "status": "pending",
    }
    assert result.output["order_authority"] is False
    assert result.output["court_authority"] is False
    assert result.artifacts == ("approval-request",)
    pending = approvals.list_pending()
    assert len(pending) == 1
    assert pending[0].request_id == "approval-001"
    assert approval_path.exists()


def test_queue_purchase_request_rejects_duplicate_review(tmp_path: Path) -> None:
    skill, _, _ = _build_skill(tmp_path)
    inputs = {
        "approval_request_id": "approval-001",
        "requirement_id": "req-001",
        "candidate_id": "cand-001",
        "requested_by": "procurement-agent",
    }
    skill.run(inputs)

    with pytest.raises(ValueError):
        skill.run(inputs)


def test_queue_purchase_request_rejects_order_input(tmp_path: Path) -> None:
    skill, approvals, approval_path = _build_skill(tmp_path)

    with pytest.raises(ValueError, match="exact declared inputs"):
        skill.run(
            {
                "approval_request_id": "approval-001",
                "requirement_id": "req-001",
                "candidate_id": "cand-001",
                "requested_by": "procurement-agent",
                "place_order": True,
            }
        )
    assert approvals.list_pending() == ()
    assert not approval_path.exists()
