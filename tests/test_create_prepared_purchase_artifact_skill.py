from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.prepared_purchase_artifacts import (
    PreparedPurchaseArtifact,
    PreparedPurchaseArtifactStore,
)
from business_agents.procurement import SupplierCandidate, SupplierCandidateStore
from business_agents.procurement_requirements import ProcurementRequirement, ProcurementRequirementStore
from business_agents.skills.create_prepared_purchase_artifact import (
    CreatePreparedPurchaseArtifactSkill,
)
from business_agents.skills.prepare_purchase_request import PreparePurchaseRequestSkill


def build_skill(tmp_path: Path):
    requirements = ProcurementRequirementStore(tmp_path / "requirements.jsonl")
    candidates = SupplierCandidateStore(tmp_path / "candidates.jsonl")
    artifacts = PreparedPurchaseArtifactStore(tmp_path / "artifacts.jsonl")
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
    prepare = PreparePurchaseRequestSkill(requirements, candidates)
    return CreatePreparedPurchaseArtifactSkill(prepare, artifacts), artifacts


def test_artifact_round_trip_binds_commercial_terms(tmp_path: Path) -> None:
    skill, store = build_skill(tmp_path)
    result = skill.run(
        {
            "artifact_id": "purchase-001",
            "requirement_id": "req-001",
            "candidate_id": "cand-001",
            "delivery_destination_reference": "destination://main-workshop",
        }
    )

    artifact = store.get("purchase-001")
    assert artifact is not None
    assert artifact.supplier_name == "Supplier One"
    assert artifact.quantity == 2
    assert artifact.landed_cost == "35.00"
    assert artifact.delivery_destination_reference == "destination://main-workshop"
    assert len(artifact.payload_digest) == 64
    assert result.output["artifact"]["payload_digest"] == artifact.payload_digest
    assert result.output["order_authority"] is False


def test_digest_changes_when_commercial_term_changes(tmp_path: Path) -> None:
    skill, store = build_skill(tmp_path)
    skill.run(
        {
            "artifact_id": "purchase-001",
            "requirement_id": "req-001",
            "candidate_id": "cand-001",
            "delivery_destination_reference": "destination://main-workshop",
        }
    )
    artifact = store.get("purchase-001")
    assert artifact is not None
    changed = artifact.payload()
    changed["quantity"] = 3
    assert PreparedPurchaseArtifact.calculate_payload_digest(changed) != artifact.payload_digest


def test_invalid_digest_is_rejected(tmp_path: Path) -> None:
    skill, store = build_skill(tmp_path)
    result = skill.run(
        {
            "artifact_id": "purchase-001",
            "requirement_id": "req-001",
            "candidate_id": "cand-001",
            "delivery_destination_reference": "destination://main-workshop",
        }
    )
    payload = dict(result.output["artifact"])
    payload["payload_digest"] = "0" * 64
    with pytest.raises(ValueError, match="payload_digest"):
        PreparedPurchaseArtifact(**payload)


def test_duplicate_artifact_id_is_rejected(tmp_path: Path) -> None:
    skill, _ = build_skill(tmp_path)
    inputs = {
        "artifact_id": "purchase-001",
        "requirement_id": "req-001",
        "candidate_id": "cand-001",
        "delivery_destination_reference": "destination://main-workshop",
    }
    skill.run(inputs)
    with pytest.raises(ValueError):
        skill.run(inputs)


def test_hidden_order_input_is_rejected(tmp_path: Path) -> None:
    skill, store = build_skill(tmp_path)
    with pytest.raises(ValueError, match="exact declared inputs"):
        skill.run(
            {
                "artifact_id": "purchase-001",
                "requirement_id": "req-001",
                "candidate_id": "cand-001",
                "delivery_destination_reference": "destination://main-workshop",
                "place_order": True,
            }
        )
    assert store.get("purchase-001") is None
