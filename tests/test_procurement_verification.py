from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal
from business_agents.executors.procurement_dry_run_executor import ProcurementDryRunExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.procurement_safety_gate import ProcurementSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore, Receipt
from business_agents.procurement_intents import build_procurement_intent
from business_agents.procurement_verification import verify_procurement_dry_run


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


def run_dry_path(tmp_path):
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    intent = build_procurement_intent(lineage(), handler_id="handler-001")
    proposal = AgentProposal(
        agent_name="procurement-agent",
        intent=intent,
        rationale="Confirm reviewed procurement intent shape.",
        confidence=1.0,
    )
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=ProcurementSafetyGate(),
        executor_registry=ExecutorRegistry([ProcurementDryRunExecutor()]),
        receipt_store=receipt_store,
    )
    result = coordinator.run(
        ProcurementAgent(proposal),
        {
            "_principal_id": "principal-001",
            "_principal_session_id": "session-001",
        },
        identity_verified=True,
    )
    return intent, result, receipt_store, receipt_store.read_all()[0]


def test_verifier_accepts_matching_dry_run_evidence(tmp_path):
    intent, result, receipt_store, receipt = run_dry_path(tmp_path)

    verification = verify_procurement_dry_run(
        intent=intent,
        result=result,
        receipt=receipt,
        receipt_store=receipt_store,
    )

    assert verification.passed
    assert verification.reason == "verified-procurement-dry-run"


def test_verifier_rejects_changed_digest(tmp_path):
    intent, result, receipt_store, receipt = run_dry_path(tmp_path)
    changed = type(result)(
        executor_name=result.executor_name,
        status=result.status,
        receipt_id=result.receipt_id,
        output={**dict(result.output), "artifact_digest": "b" * 64},
    )

    verification = verify_procurement_dry_run(
        intent=intent,
        result=changed,
        receipt=receipt,
        receipt_store=receipt_store,
    )

    assert not verification.passed
    assert verification.reason == "result-digest-mismatch"


def test_verifier_rejects_changed_authorization_fingerprint(tmp_path):
    intent, result, receipt_store, receipt = run_dry_path(tmp_path)
    changed = type(result)(
        executor_name=result.executor_name,
        status=result.status,
        receipt_id=result.receipt_id,
        output={**dict(result.output), "authorization_fingerprint": "changed"},
    )

    verification = verify_procurement_dry_run(
        intent=intent,
        result=changed,
        receipt=receipt,
        receipt_store=receipt_store,
    )

    assert not verification.passed
    assert verification.reason == "authorization-fingerprint-mismatch"


def test_verifier_rejects_tampered_receipt(tmp_path):
    intent, result, receipt_store, receipt = run_dry_path(tmp_path)
    tampered = Receipt(
        receipt_id=receipt.receipt_id,
        created_at=receipt.created_at,
        actor=receipt.actor,
        decision=receipt.decision,
        executor=receipt.executor,
        subject_id="artifact-002",
        details=receipt.details,
        integrity_tag=receipt.integrity_tag,
        integrity_method=receipt.integrity_method,
    )

    verification = verify_procurement_dry_run(
        intent=intent,
        result=result,
        receipt=tampered,
        receipt_store=receipt_store,
    )

    assert not verification.passed
    assert verification.reason == "invalid-receipt"
