from decimal import Decimal
from pathlib import Path

from business_agents.procurement_requirements import (
    ProcurementRequirement,
    ProcurementRequirementStatus,
    ProcurementRequirementStore,
)


def test_requirement_round_trip_fields(tmp_path: Path) -> None:
    path = tmp_path / "requirements-roundtrip.jsonl"
    store = ProcurementRequirementStore(path)
    store.create(
        ProcurementRequirement(
            requirement_id="req-roundtrip",
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

    loaded = store.get("req-roundtrip")
    assert loaded is not None
    assert loaded.requirement_id == "req-roundtrip"
    assert loaded.target_budget == Decimal("40.00")
    assert loaded.compatibility_constraints == ("12V coil", "automotive-rated")
    assert loaded.acceptable_substitutions == ("sealed equivalent",)
    assert loaded.required_evidence == ("datasheet", "pinout")
    assert loaded.status is ProcurementRequirementStatus.RESEARCH
