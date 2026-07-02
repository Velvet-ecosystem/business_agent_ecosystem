from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.procurement_requirements import (
    ProcurementRequirement,
    ProcurementRequirementStatus,
    ProcurementRequirementStore,
)


def _requirement(requirement_id: str = "req-001") -> ProcurementRequirement:
    return ProcurementRequirement(
        requirement_id=requirement_id,
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


def test_requirement_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "requirements.jsonl"
    store = ProcurementRequirementStore(path)
    requirement = _requirement()
    store.create(requirement)

    loaded = store.get("req-001")
    assert loaded == requirement
    assert loaded.status is ProcurementRequirementStatus.RESEARCH


def test_requirement_requires_constraints_and_evidence() -> None:
    with pytest.raises(ValueError, match="constraints and required evidence"):
        ProcurementRequirement(
            requirement_id="req-001",
            item_name="Relay",
            quantity=1,
            intended_use="Test",
            compatibility_constraints=(),
            acceptable_substitutions=(),
            target_budget=Decimal("10.00"),
            currency="CAD",
            required_evidence=(),
            urgency="normal",
            source_reference="job://job-001",
        )


def test_requirement_rejects_duplicate_id(tmp_path: Path) -> None:
    store = ProcurementRequirementStore(tmp_path / "requirements.jsonl")
    requirement = _requirement()
    store.create(requirement)

    with pytest.raises(ValueError):
        store.create(requirement)


def test_requirement_rejects_negative_budget() -> None:
    with pytest.raises(ValueError, match="target_budget"):
        ProcurementRequirement(
            requirement_id="req-001",
            item_name="Relay",
            quantity=1,
            intended_use="Test",
            compatibility_constraints=("12V",),
            acceptable_substitutions=(),
            target_budget=Decimal("-1.00"),
            currency="CAD",
            required_evidence=("datasheet",),
            urgency="normal",
            source_reference="job://job-001",
        )
