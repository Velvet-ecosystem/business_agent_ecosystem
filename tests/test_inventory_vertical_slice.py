from pathlib import Path

import pytest

from business_agents.agents.inventory_agent import InventoryAgent
from business_agents.contracts import BusinessIntent
from business_agents.executors.registry import ExecutorRegistry
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_gate import InternalTaskSafetyGate


def make_coordinator(tmp_path: Path) -> tuple[BusinessCoordinator, TaskExecutor]:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    executor = TaskExecutor(receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=InternalTaskSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )
    return coordinator, executor


def low_stock_context() -> dict[str, object]:
    return {
        "sku": "FILTER-001",
        "location": "small-workshop",
        "on_hand": 2,
        "reorder_point": 8,
        "suggested_quantity": 12,
    }


def test_inventory_agent_creates_internal_task_and_receipt(tmp_path: Path) -> None:
    coordinator, executor = make_coordinator(tmp_path)
    result = coordinator.run(
        InventoryAgent(),
        low_stock_context(),
        identity_verified=True,
    )

    assert result.status == "completed"
    assert result.receipt_id.startswith("rcpt_")
    assert len(executor.tasks) == 1
    assert "FILTER-001" in executor.tasks[0].title

    receipts = executor.receipt_store.read_all()
    assert len(receipts) == 1
    assert receipts[0].decision == "completed"
    assert receipts[0].details["authorization_id"].startswith("auth:")
    assert receipts[0].details["route"] == "internal-task"
    assert receipts[0].details["action"] == "create-restock-review"
    assert executor.receipt_store.verify(receipts[0]) is True


def test_inventory_flow_denies_unverified_identity(tmp_path: Path) -> None:
    coordinator, executor = make_coordinator(tmp_path)

    with pytest.raises(PermissionError, match="identity-not-verified"):
        coordinator.run(
            InventoryAgent(),
            low_stock_context(),
            identity_verified=False,
        )

    assert executor.tasks == []
    receipts = executor.receipt_store.read_all()
    assert len(receipts) == 1
    assert receipts[0].decision == "denied"
    assert receipts[0].details["reason"] == "identity-not-verified"
    assert receipts[0].details["identity_verified"] is False
    assert executor.receipt_store.verify(receipts[0]) is True


def test_safety_gate_rejects_excessive_quantity(tmp_path: Path) -> None:
    coordinator, executor = make_coordinator(tmp_path)
    context = low_stock_context()
    context["suggested_quantity"] = 101

    with pytest.raises(PermissionError, match="safety-check-failed"):
        coordinator.run(
            InventoryAgent(),
            context,
            identity_verified=True,
        )

    assert executor.tasks == []
    receipts = executor.receipt_store.read_all()
    assert len(receipts) == 1
    assert receipts[0].decision == "denied"
    assert receipts[0].details["safety_reason"] == "quantity-exceeds-limit"


def test_missing_executor_is_denied_and_receipted(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=InternalTaskSafetyGate(),
        executor_registry=ExecutorRegistry(),
        receipt_store=receipt_store,
    )

    with pytest.raises(PermissionError, match="executor-not-available"):
        coordinator.run(
            InventoryAgent(),
            low_stock_context(),
            identity_verified=True,
        )

    receipts = receipt_store.read_all()
    assert len(receipts) == 1
    assert receipts[0].actor == "Executor Registry"
    assert receipts[0].decision == "denied"
    assert receipts[0].details["reason"] == "executor-not-available"
    assert receipts[0].details["authorization_id"].startswith("auth:")


def test_safety_gate_rejects_missing_sku() -> None:
    decision = InternalTaskSafetyGate().evaluate(
        BusinessIntent(
            route="internal-task",
            action="create-restock-review",
            subject_id="small-workshop",
            parameters={"suggested_quantity": 12},
        )
    )

    assert decision.passed is False
    assert decision.reason == "invalid-sku"


def test_safety_gate_rejects_boolean_quantity() -> None:
    decision = InternalTaskSafetyGate().evaluate(
        BusinessIntent(
            route="internal-task",
            action="create-restock-review",
            subject_id="small-workshop",
            parameters={"sku": "FILTER-001", "suggested_quantity": True},
        )
    )

    assert decision.passed is False
    assert decision.reason == "invalid-quantity"
