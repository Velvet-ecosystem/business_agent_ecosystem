from pathlib import Path

import pytest

from business_agents.agents.inventory_agent import InventoryAgent
from business_agents.agents.operations_note_agent import OperationsNoteAgent
from business_agents.executors.note_executor import NoteExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.internal_note_safety import InternalNoteSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_gate import InternalTaskSafetyGate
from business_agents.gateway.safety_registry import SafetyGateRegistry


def make_coordinator(
    tmp_path: Path,
) -> tuple[BusinessCoordinator, TaskExecutor, NoteExecutor, JsonlReceiptStore]:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    task_executor = TaskExecutor(receipt_store)
    note_executor = NoteExecutor(receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=SafetyGateRegistry(
            [InternalTaskSafetyGate(), InternalNoteSafetyGate()]
        ),
        executor_registry=ExecutorRegistry([task_executor, note_executor]),
        receipt_store=receipt_store,
    )
    return coordinator, task_executor, note_executor, receipt_store


def note_context() -> dict[str, str]:
    return {
        "subject_id": "small-workshop",
        "title": "Printer maintenance",
        "body": "Cleaned the rails and checked belt tension.",
    }


def test_registry_routes_two_distinct_executor_paths(tmp_path: Path) -> None:
    coordinator, task_executor, note_executor, receipts = make_coordinator(tmp_path)

    task_result = coordinator.run(
        InventoryAgent(),
        {
            "sku": "FILTER-001",
            "location": "small-workshop",
            "on_hand": 2,
            "reorder_point": 8,
            "suggested_quantity": 12,
        },
        identity_verified=True,
    )
    note_result = coordinator.run(
        OperationsNoteAgent(), note_context(), identity_verified=True
    )

    assert task_result.executor_name == "Task Executor"
    assert note_result.executor_name == "Note Executor"
    assert len(task_executor.tasks) == 1
    assert len(note_executor.notes) == 1
    assert len(receipts.read_all()) == 2


def test_internal_note_is_receipted(tmp_path: Path) -> None:
    coordinator, _, note_executor, receipt_store = make_coordinator(tmp_path)

    result = coordinator.run(
        OperationsNoteAgent(), note_context(), identity_verified=True
    )

    assert result.status == "completed"
    assert result.output["note_id"] == "note_0001"
    assert note_executor.notes[0].body.startswith("Cleaned the rails")
    receipt = receipt_store.read_all()[0]
    assert receipt.executor == "Note Executor"
    assert receipt.details["route"] == "internal-note"
    assert receipt.details["action"] == "record-operations-note"
    assert receipt_store.verify(receipt) is True


def test_oversized_note_is_denied_before_execution(tmp_path: Path) -> None:
    coordinator, _, note_executor, receipt_store = make_coordinator(tmp_path)
    context = note_context()
    context["body"] = "x" * 2001

    with pytest.raises(PermissionError, match="safety-check-failed"):
        coordinator.run(
            OperationsNoteAgent(), context, identity_verified=True
        )

    assert note_executor.notes == []
    receipt = receipt_store.read_all()[0]
    assert receipt.decision == "denied"
    assert receipt.details["safety_reason"] == "body-too-long"


def test_external_note_fields_are_rejected() -> None:
    decision = InternalNoteSafetyGate().evaluate(
        OperationsNoteAgent().propose(note_context()).intent.__class__(
            route="internal-note",
            action="record-operations-note",
            subject_id="small-workshop",
            parameters={
                "title": "Send update",
                "body": "Send this outside the system.",
                "email": "someone@example.com",
            },
        )
    )

    assert decision.passed is False
    assert decision.reason == "external-fields-forbidden"
