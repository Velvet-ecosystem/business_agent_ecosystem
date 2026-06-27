"""Tests for the bounded customer intake vertical slice."""

from pathlib import Path

import pytest

from business_agents.agents.intake_agent import IntakeAgent
from business_agents.contracts import BusinessIntent
from business_agents.executors.registry import ExecutorRegistry
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_gate import InternalTaskSafetyGate


def valid_context() -> dict[str, str]:
    return {
        "customer_name": "Alex Morgan",
        "contact": "alex@example.com",
        "request": "Install a Velvet system in a 2008 Hyundai Tiburon.",
        "source": "website-form",
    }


def test_intake_agent_creates_internal_review_proposal() -> None:
    proposal = IntakeAgent().propose(valid_context())
    assert proposal.agent_name == "Intake Agent"
    assert proposal.intent.route == "internal-task"
    assert proposal.intent.action == "create-intake-review"
    assert proposal.intent.subject_id.startswith("lead:")
    assert proposal.authority_granted is False


def test_intake_requires_contact_and_request() -> None:
    context = valid_context()
    context["contact"] = ""
    with pytest.raises(ValueError, match="contact is required"):
        IntakeAgent().propose(context)


def test_intake_request_length_is_bounded() -> None:
    context = valid_context()
    context["request"] = "x" * 2001
    with pytest.raises(ValueError, match="request is too long"):
        IntakeAgent().propose(context)


def test_safety_gate_rejects_external_action_fields() -> None:
    intent = BusinessIntent(
        route="internal-task",
        action="create-intake-review",
        subject_id="lead:alex",
        parameters={**valid_context(), "send_message": True},
    )
    decision = InternalTaskSafetyGate().evaluate(intent)
    assert decision.passed is False
    assert decision.reason == "external-or-financial-fields-forbidden"


def test_intake_flow_creates_receipted_internal_task(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    executor = TaskExecutor(receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=InternalTaskSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )
    result = coordinator.run(IntakeAgent(), valid_context(), identity_verified=True)
    assert result.status == "completed"
    assert result.output["task_id"] == "task_0001"
    assert "Alex Morgan" in result.output["title"]
    assert len(executor.tasks) == 1
    assert executor.tasks[0].metadata["contact"] == "alex@example.com"
    assert result.receipt_id


def test_unverified_identity_cannot_create_intake_task(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    executor = TaskExecutor(receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=InternalTaskSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )
    with pytest.raises(PermissionError, match="identity-not-verified"):
        coordinator.run(IntakeAgent(), valid_context(), identity_verified=False)
    assert executor.tasks == []
