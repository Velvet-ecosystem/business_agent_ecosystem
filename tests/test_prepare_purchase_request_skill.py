from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.procurement import SupplierCandidate, SupplierCandidateStore
from business_agents.procurement_requirements import (
    ProcurementRequirement,
    ProcurementRequirementStatus,
    ProcurementRequirementStore,
)
from business_agents.skills.prepare_purchase_request import PreparePurchaseRequestSkill


def _requirement(
    status: ProcurementRequirementStatus = ProcurementRequirementStatus.RESEARCH,
) -> ProcurementRequirement:
    return ProcurementRequirement(
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
        status=status,
    )


def _candidate(
    *,
    candidate_id: str = "cand-001",
    quantity: int = 2,
    currency: str = "CAD",
    unit_price: str = "15.00",
    shipping: str = "5.00",
    risk_flags: tuple[str, ...] = (),
) -> SupplierCandidate:
    return SupplierCandidate(
        candidate_id=candidate_id,
        requirement_id="req-001",
        supplier_name="Supplier One",
        supplier_part_number="SUP-001",
        manufacturer_part_number="MPN-001",
        quantity=quantity,
        unit_price=Decimal(unit_price),
        shipping_cost=Decimal(shipping),
        currency=currency,
        source_reference="source://candidate-001",
        compatibility_evidence=("datasheet-pinout-match",),
        risk_flags=risk_flags,
    )


def _stores(tmp_path: Path) -> tuple[ProcurementRequirementStore, SupplierCandidateStore]:
    return (
        ProcurementRequirementStore(tmp_path / "requirements.jsonl"),
        SupplierCandidateStore(tmp_path / "candidates.jsonl"),
    )


def test_prepare_purchase_request_is_read_only_and_non_ordering(tmp_path: Path) -> None:
    requirements, candidates = _stores(tmp_path)
    requirements.create(_requirement())
    candidates.create(_candidate())
    requirement_path = tmp_path / "requirements.jsonl"
    candidate_path = tmp_path / "candidates.jsonl"
    before_requirements = requirement_path.read_text(encoding="utf-8")
    before_candidates = candidate_path.read_text(encoding="utf-8")

    result = PreparePurchaseRequestSkill(requirements, candidates).run(
        {"requirement_id": "req-001", "candidate_id": "cand-001"}
    )

    assert result.output["purchase_request"] == {
        "requirement_id": "req-001",
        "candidate_id": "cand-001",
        "item_name": "Automotive relay",
        "intended_use": "Isolated accessory control",
        "supplier_name": "Supplier One",
        "supplier_part_number": "SUP-001",
        "manufacturer_part_number": "MPN-001",
        "quantity": 2,
        "currency": "CAD",
        "unit_price": "15.00",
        "shipping_cost": "5.00",
        "landed_cost": "35.00",
        "target_budget": "40.00",
        "source_reference": "source://candidate-001",
        "compatibility_evidence": ("datasheet-pinout-match",),
        "required_approval": "strong-human",
    }
    assert result.output["review_flags"] == ()
    assert result.output["order_authority"] is False
    assert result.artifacts == ("prepared-purchase-request",)
    assert requirement_path.read_text(encoding="utf-8") == before_requirements
    assert candidate_path.read_text(encoding="utf-8") == before_candidates


def test_prepare_purchase_request_surfaces_review_flags(tmp_path: Path) -> None:
    requirements, candidates = _stores(tmp_path)
    requirements.create(_requirement())
    candidates.create(
        _candidate(
            quantity=3,
            currency="USD",
            unit_price="20.00",
            shipping="5.00",
            risk_flags=("marketplace-seller",),
        )
    )

    result = PreparePurchaseRequestSkill(requirements, candidates).run(
        {"requirement_id": "req-001", "candidate_id": "cand-001"}
    )

    assert result.output["review_flags"] == (
        "marketplace-seller",
        "currency-mismatch",
        "quantity-mismatch",
    )


def test_prepare_purchase_request_flags_over_budget(tmp_path: Path) -> None:
    requirements, candidates = _stores(tmp_path)
    requirements.create(_requirement())
    candidates.create(_candidate(unit_price="20.00", shipping="5.00"))

    result = PreparePurchaseRequestSkill(requirements, candidates).run(
        {"requirement_id": "req-001", "candidate_id": "cand-001"}
    )

    assert result.output["review_flags"] == ("over-target-budget",)


def test_prepare_purchase_request_rejects_closed_requirement(tmp_path: Path) -> None:
    requirements, candidates = _stores(tmp_path)
    requirements.create(_requirement(ProcurementRequirementStatus.CANCELLED))
    candidates.create(_candidate())

    with pytest.raises(ValueError, match="not open"):
        PreparePurchaseRequestSkill(requirements, candidates).run(
            {"requirement_id": "req-001", "candidate_id": "cand-001"}
        )


def test_prepare_purchase_request_rejects_orphan_candidate(tmp_path: Path) -> None:
    requirements, candidates = _stores(tmp_path)
    requirements.create(_requirement())

    with pytest.raises(ValueError, match="candidate not found"):
        PreparePurchaseRequestSkill(requirements, candidates).run(
            {"requirement_id": "req-001", "candidate_id": "cand-missing"}
        )


def test_prepare_purchase_request_rejects_order_input(tmp_path: Path) -> None:
    requirements, candidates = _stores(tmp_path)
    skill = PreparePurchaseRequestSkill(requirements, candidates)

    with pytest.raises(ValueError, match="exact declared inputs"):
        skill.run(
            {
                "requirement_id": "req-001",
                "candidate_id": "cand-001",
                "place_order": True,
            }
        )
