from pathlib import Path

import pytest

from business_agents.approval_requests import ApprovalRequestStore
from business_agents.prepared_purchase_artifacts import PreparedPurchaseArtifact, PreparedPurchaseArtifactStore
from business_agents.skills.queue_purchase_request import QueuePurchaseRequestSkill


def make_artifact() -> PreparedPurchaseArtifact:
    payload = {
        "artifact_id": "artifact-001",
        "requirement_id": "req-001",
        "candidate_id": "cand-001",
        "item_name": "Automotive relay",
        "intended_use": "Accessory control",
        "supplier_name": "Supplier One",
        "supplier_part_number": "SUP-001",
        "manufacturer_part_number": "MPN-001",
        "quantity": 2,
        "currency": "CAD",
        "unit_price": "15.00",
        "shipping_cost": "5.00",
        "landed_cost": "35.00",
        "target_budget": "40.00",
        "delivery_destination_reference": "destination://workshop",
        "source_reference": "source://candidate-001",
        "compatibility_evidence": ("datasheet-match",),
        "review_flags": (),
        "required_approval": "strong-human",
    }
    digest = PreparedPurchaseArtifact.calculate_payload_digest(payload)
    return PreparedPurchaseArtifact(**payload, payload_digest=digest)


def build_skill(tmp_path: Path):
    artifacts = PreparedPurchaseArtifactStore(tmp_path / "artifacts.jsonl")
    approvals = ApprovalRequestStore(tmp_path / "approvals.jsonl")
    artifact = make_artifact()
    artifacts.create(artifact)
    return QueuePurchaseRequestSkill(artifacts, approvals), approvals, artifact


def test_queue_binds_exact_artifact(tmp_path: Path) -> None:
    skill, approvals, artifact = build_skill(tmp_path)
    result = skill.run(
        {
            "approval_request_id": "approval-001",
            "artifact_id": "artifact-001",
            "requested_by": "procurement-agent",
        }
    )

    request = result.output["approval_request"]
    assert request["subject_id"] == "artifact-001"
    assert artifact.payload_digest in request["summary"]
    assert result.output["artifact_digest"] == artifact.payload_digest
    assert result.output["order_authority"] is False
    assert result.output["court_authority"] is False
    assert approvals.list_pending()[0].subject_id == "artifact-001"


def test_queue_rejects_missing_artifact(tmp_path: Path) -> None:
    artifacts = PreparedPurchaseArtifactStore(tmp_path / "artifacts.jsonl")
    approvals = ApprovalRequestStore(tmp_path / "approvals.jsonl")
    skill = QueuePurchaseRequestSkill(artifacts, approvals)

    with pytest.raises(ValueError, match="artifact not found"):
        skill.run(
            {
                "approval_request_id": "approval-001",
                "artifact_id": "missing",
                "requested_by": "procurement-agent",
            }
        )


def test_queue_rejects_duplicate_id(tmp_path: Path) -> None:
    skill, _, _ = build_skill(tmp_path)
    inputs = {
        "approval_request_id": "approval-001",
        "artifact_id": "artifact-001",
        "requested_by": "procurement-agent",
    }
    skill.run(inputs)
    with pytest.raises(ValueError):
        skill.run(inputs)


def test_queue_rejects_extra_input(tmp_path: Path) -> None:
    skill, approvals, _ = build_skill(tmp_path)
    with pytest.raises(ValueError, match="exact declared inputs"):
        skill.run(
            {
                "approval_request_id": "approval-001",
                "artifact_id": "artifact-001",
                "requested_by": "procurement-agent",
                "extra": True,
            }
        )
    assert approvals.list_pending() == ()
