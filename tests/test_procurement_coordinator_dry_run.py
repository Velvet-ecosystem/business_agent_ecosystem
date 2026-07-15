from typing import Any, Mapping

import pytest

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal
from business_agents.executors.procurement_dry_run_executor import ProcurementDryRunExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.procurement_safety_gate import ProcurementSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.procurement_intents import build_procurement_intent


def lineage(**changes):
    values = {
        "approval_request_id": "approval-001",
        "decision_id": "decision-001",
        "artifact_id": "artifact-001",
        "artifact_digest": "a" * 64,
        "route": "procurement.order",
        "action": "place-bounded-order",
        "subject_id": "artifact-001",
        "risk_level": "high",
        "approval_mode": "strong-human",
        "bounded_to_exact_artifact_digest": True,
    }
    values.update(changes)
    return values


class ProcurementAgent(BaseAgent):
    def __init__(self, proposal: AgentProposal) -> None:
        super().__init__("procurement-agent")
        self._proposal = proposal

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        return self._proposal


def make_coordinator(receipt_store: JsonlReceiptStore) -> BusinessCoordinator:
    return BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=ProcurementSafetyGate(),
        executor_registry=ExecutorRegistry([ProcurementDryRunExecutor()]),
        receipt_store=receipt_store,
    )


def test_procurement_intent_runs_through_existing_coordinator(tmp_path):
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    intent = build_procurement_intent(lineage(), handler_id="handler-001")
    proposal = AgentProposal(
        agent_name="procurement-agent",
        intent=intent,
        rationale="Confirm reviewed procurement intent shape.",
        confidence=1.0,
    )

    result = make_coordinator(receipt_store).run(
        ProcurementAgent(proposal),
        {
            "_principal_id": "principal-001",
            "_principal_session_id": "session-001",
            "_principal_display_name": "Mister",
            "_principal_role": "owner",
            "_principal_presence_level": "local",
        },
        identity_verified=True,
    )

    assert result.executor_name == "procurement-dry-run"
    assert result.status == "completed"
    assert result.output["artifact_id"] == "artifact-001"
    assert result.output["artifact_digest"] == "a" * 64
    assert result.output["handler_id"] == "handler-001"
    assert result.output["external_action"] is False
    assert result.output["authorization_id"]
    assert result.output["authorization_fingerprint"]

    receipts = receipt_store.read_all()
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt_store.verify(receipt)
    assert receipt.actor == "Court"
    assert receipt.decision == "authorized"
    assert receipt.subject_id == "artifact-001"
    assert receipt.details["route"] == "procurement.order"
    assert receipt.details["action"] == "place-bounded-order"
    assert receipt.details["principal_id"] == "principal-001"
    assert receipt.details["principal_session_id"] == "session-001"
    assert receipt.details["authorization_id"] == result.output["authorization_id"]
    assert receipt.details["authorization_fingerprint"] == result.output["authorization_fingerprint"]


def test_procurement_coordinator_rejects_safety_failure(tmp_path):
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    intent = build_procurement_intent(lineage(), handler_id="handler-001")
    bad_intent = type(intent)(
        route=intent.route,
        action=intent.action,
        subject_id="artifact-002",
        parameters=dict(intent.parameters),
        risk_level=intent.risk_level,
        approval_mode=intent.approval_mode,
    )
    proposal = AgentProposal(
        agent_name="procurement-agent",
        intent=bad_intent,
        rationale="Invalid shape should fail safety.",
        confidence=1.0,
    )

    with pytest.raises(PermissionError, match="safety-check-failed"):
        make_coordinator(receipt_store).run(ProcurementAgent(proposal), {}, identity_verified=True)

    receipts = receipt_store.read_all()
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt_store.verify(receipt)
    assert receipt.actor == "Court"
    assert receipt.decision == "denied"
    assert receipt.subject_id == "artifact-002"
    assert receipt.details["reason"] == "safety-check-failed"
    assert receipt.details["safety_reason"] == "subject-artifact-mismatch"
    assert receipt.details["identity_verified"] is True
    assert receipt.details["safety_passed"] is False
