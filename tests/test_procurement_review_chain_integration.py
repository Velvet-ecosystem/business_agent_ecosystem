from datetime import datetime, timedelta, timezone
from pathlib import Path

from business_agents.approval_decisions import (
    ApprovalDecision,
    ApprovalDecisionStore,
    ApprovalDecisionValue,
)
from business_agents.approval_requests import ApprovalRequestStore
from business_agents.bound_artifact_scope import BoundArtifactScope
from business_agents.bounded_action_ticket import BoundedActionTicket
from business_agents.prepared_purchase_artifacts import (
    PreparedPurchaseArtifact,
    PreparedPurchaseArtifactStore,
)
from business_agents.skills.prepare_decision_lineage import PrepareDecisionLineageSkill
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
    return PreparedPurchaseArtifact(
        **payload,
        payload_digest=PreparedPurchaseArtifact.calculate_payload_digest(payload),
    )


def test_review_chain_preserves_exact_artifact_without_action(tmp_path: Path) -> None:
    artifacts = PreparedPurchaseArtifactStore(tmp_path / "artifacts.jsonl")
    approvals = ApprovalRequestStore(tmp_path / "approvals.jsonl")
    decisions = ApprovalDecisionStore(tmp_path / "decisions.jsonl")
    artifact = make_artifact()
    artifacts.create(artifact)

    queued = QueuePurchaseRequestSkill(artifacts, approvals).run(
        {
            "approval_request_id": "approval-001",
            "artifact_id": artifact.artifact_id,
            "requested_by": "test-agent",
        }
    )
    assert queued.output["artifact_digest"] == artifact.payload_digest
    assert queued.output["order_authority"] is False
    assert queued.output["court_authority"] is False

    decisions.create(
        ApprovalDecision(
            decision_id="decision-001",
            request_id="approval-001",
            decision=ApprovalDecisionValue.APPROVE,
            decided_by="Mister",
            rationale="Reviewed exact artifact.",
            strong_confirmation=True,
        )
    )

    lineage = PrepareDecisionLineageSkill(approvals, decisions, artifacts).run(
        {"request_id": "approval-001"}
    )
    package = lineage.output["lineage_package"]
    assert package["artifact_id"] == artifact.artifact_id
    assert package["artifact_digest"] == artifact.payload_digest
    assert lineage.output["authority_granted"] is False
    assert lineage.output["action_performed"] is False

    binding = BoundArtifactScope(
        artifact_id=package["artifact_id"],
        artifact_digest=package["artifact_digest"],
        route=package["route"],
        action=package["action"],
        subject_id=package["subject_id"],
        handler_id="handler-001",
    )
    now = datetime(2026, 7, 3, 12, 0, tzinfo=timezone.utc)
    record = BoundedActionTicket(
        ticket_id="ticket-001",
        approval_request_id=package["approval_request_id"],
        decision_id=package["decision_id"],
        binding=binding,
        issued_by="Court",
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    assert record.matches(
        artifact_id=artifact.artifact_id,
        artifact_digest=artifact.payload_digest,
        route=package["route"],
        action=package["action"],
        subject_id=artifact.artifact_id,
        handler_id="handler-001",
    )
    assert not record.matches(
        artifact_id=artifact.artifact_id,
        artifact_digest="b" * 64,
        route=package["route"],
        action=package["action"],
        subject_id=artifact.artifact_id,
        handler_id="handler-001",
    )
