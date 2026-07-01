from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.procurement import SupplierCandidate, SupplierCandidateStore
from business_agents.skills.supplier_candidate_comparison import SupplierCandidateComparisonSkill


def _candidate(candidate_id: str, supplier: str, unit: str, shipping: str) -> SupplierCandidate:
    return SupplierCandidate(
        candidate_id=candidate_id,
        requirement_id="req-001",
        supplier_name=supplier,
        supplier_part_number=f"SUP-{candidate_id}",
        manufacturer_part_number="MPN-001",
        quantity=2,
        unit_price=Decimal(unit),
        shipping_cost=Decimal(shipping),
        currency="CAD",
        source_reference=f"source://{candidate_id}",
        compatibility_evidence=("datasheet-pinout-match",),
        risk_flags=("marketplace-seller",) if candidate_id == "cand-002" else (),
    )


def test_supplier_candidate_requires_compatibility_evidence() -> None:
    with pytest.raises(ValueError, match="compatibility_evidence"):
        SupplierCandidate(
            candidate_id="cand-001",
            requirement_id="req-001",
            supplier_name="Supplier",
            supplier_part_number="SUP-1",
            manufacturer_part_number="MPN-1",
            quantity=1,
            unit_price=Decimal("1.00"),
            shipping_cost=Decimal("0.00"),
            currency="CAD",
            source_reference="source://1",
            compatibility_evidence=(),
        )


def test_supplier_comparison_is_read_only_and_non_purchasing(tmp_path: Path) -> None:
    path = tmp_path / "suppliers.jsonl"
    store = SupplierCandidateStore(path)
    store.create(_candidate("cand-002", "Supplier Two", "8.00", "5.00"))
    store.create(_candidate("cand-001", "Supplier One", "10.00", "0.00"))

    before = path.read_text(encoding="utf-8")
    result = SupplierCandidateComparisonSkill(store).run({"requirement_id": "req-001"})
    after = path.read_text(encoding="utf-8")

    assert result.output["candidate_count"] == 2
    assert result.output["currencies"] == ("CAD",)
    assert result.output["purchase_authority"] is False
    assert result.output["candidates"][0]["candidate_id"] == "cand-001"
    assert result.output["candidates"][0]["landed_cost"] == "20.00"
    assert result.output["candidates"][1]["landed_cost"] == "21.00"
    assert result.output["candidates"][1]["risk_flags"] == ("marketplace-seller",)
    assert before == after


def test_supplier_comparison_rejects_purchase_input(tmp_path: Path) -> None:
    skill = SupplierCandidateComparisonSkill(SupplierCandidateStore(tmp_path / "suppliers.jsonl"))

    with pytest.raises(ValueError, match="requires only requirement_id"):
        skill.run({"requirement_id": "req-001", "purchase": True})


def test_supplier_store_rejects_duplicate_candidates(tmp_path: Path) -> None:
    store = SupplierCandidateStore(tmp_path / "suppliers.jsonl")
    candidate = _candidate("cand-001", "Supplier One", "10.00", "0.00")
    store.create(candidate)

    with pytest.raises(ValueError):
        store.create(candidate)
