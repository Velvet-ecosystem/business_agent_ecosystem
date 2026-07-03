from pathlib import Path

import pytest

from business_agents.approval_decisions import ApprovalDecision, ApprovalDecisionStore, ApprovalDecisionValue
from business_agents.approval_requests import ApprovalRequest, ApprovalRequestStore
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.prepared_purchase_artifacts import PreparedPurchaseArtifact, PreparedPurchaseArtifactStore
from business_agents.skills.prepare_decision_lineage import PrepareDecisionLineageSkill


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
    return PreparedPurchaseArtifact(
        **payload,
        payload_digest=PreparedPurchaseArtifact.calculate_payload_digest(payload),
    )


def stores(tmp_path: Path):
    return (
        ApprovalRequestStore(tmp_path / "requests.jsonl"),
        ApprovalDecisionStore(tmp_path / "decisions.jsonl"),
        PreparedPurchaseArtifactStore(tmp_path / "artifacts.jsonl"),
    )


def make_request(subject_id: str = "artifact-001") -> ApprovalRequest:
    return ApprovalRequest(
        request_id="approval-001",
        route="example.route",
        action="example-action",
        subject_id=subject_id,
        summary="Review artifact",
        requested_by="test-agent",
        risk_level=RiskLevel.HIGH,
        approval_mode=ApprovalMode.STRONG_HUMAN,
    )


def make_decision(value: ApprovalDecisionValue) -> ApprovalDecision:
    return ApprovalDecision(
        decision_id="decision-001",
        request_id="approval-001",
        decision=value,
        decided_by="Mister",
        rationale="Reviewed.",
        strong_confirmation=value is ApprovalDecisionValue.APPROVE,
    )


def test_lineage_carries_exact_artifact_digest(tmp_path: Path) -> None:
    requests, decisions, artifacts = stores(tmp_path)
    artifact = make_artifact()
    artifacts.create(artifact)
    requests.create(make_request())
    decisions.create(make_decision(ApprovalDecisionValue.APPROVE))

    result = PrepareDecisionLineageSkill(requests, decisions, artifacts).run(
        {"request_id": "approval-001"}
    )
    package = result.output["lineage_package"]
    assert package["artifact_id"] == "artifact-001"
    assert package["artifact_digest"] == artifact.payload_digest
    assert package["subject_id"] == "artifact-001"
    assert package["bounded_to_exact_artifact_digest"] is True
    assert result.output["authority_granted"] is False
    assert result.output["action_performed"] is False


def test_missing_artifact_is_rejected(tmp_path: Path) -> None:
    requests, decisions, artifacts = stores(tmp_path)
    requests.create(make_request())
    decisions.create(make_decision(ApprovalDecisionValue.APPROVE))
    with pytest.raises(ValueError, match="artifact not found"):
        PrepareDecisionLineageSkill(requests, decisions, artifacts).run(
            {"request_id": "approval-001"}
        )


def test_denied_decision_is_rejected(tmp_path: Path) -> None:
    requests, decisions, artifacts = stores(tmp_path)
    artifacts.create(make_artifact())
    requests.create(make_request())
    decisions.create(make_decision(ApprovalDecisionValue.DENY))
    with pytest.raises(ValueError, match="not approved"):
        PrepareDecisionLineageSkill(requests, decisions, artifacts).run(
            {"request_id": "approval-001"}
        )


def test_extra_input_is_rejected(tmp_path: Path) -> None:
    requests, decisions, artifacts = stores(tmp_path)
    with pytest.raises(ValueError, match="requires only request_id"):
        PrepareDecisionLineageSkill(requests, decisions, artifacts).run(
            {"request_id": "approval-001", "extra": True}
        )
