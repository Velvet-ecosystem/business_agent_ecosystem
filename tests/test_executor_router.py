from pathlib import Path

import pytest

from business_agents.agents.inventory_agent import InventoryAgent
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_gate import InternalTaskSafetyGate


class UnsupportedExecutor(BaseExecutor):
    route = "document"
    allowed_actions = frozenset({"archive"})

    def execute(
        self,
        intent: BusinessIntent,
        *,
        authorization_id: str,
    ) -> ExecutorResult:
        raise AssertionError("unsupported executor must not run")


def low_stock_context() -> dict[str, object]:
    return {
        "sku": "FILTER-001",
        "location": "small-workshop",
        "on_hand": 2,
        "reorder_point": 8,
        "suggested_quantity": 12,
    }


def test_coordinator_rejects_empty_executor_registry(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")

    with pytest.raises(ValueError, match="at least one executor is required"):
        BusinessCoordinator(
            court=CourtPolicy(),
            safety_gate=InternalTaskSafetyGate(),
            executors=[],
            receipt_store=receipt_store,
        )


def test_no_matching_executor_is_denied_and_receipted(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=InternalTaskSafetyGate(),
        executors=[UnsupportedExecutor()],
        receipt_store=receipt_store,
    )

    with pytest.raises(LookupError, match="no-matching-executor"):
        coordinator.run(
            InventoryAgent(),
            low_stock_context(),
            identity_verified=True,
        )

    receipts = receipt_store.read_all()
    assert len(receipts) == 1
    assert receipts[0].decision == "denied"
    assert receipts[0].details["reason"] == "no-matching-executor"


def test_ambiguous_executor_route_is_denied_and_receipted(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    first = TaskExecutor(receipt_store)
    second = TaskExecutor(receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=InternalTaskSafetyGate(),
        executors=[first, second],
        receipt_store=receipt_store,
    )

    with pytest.raises(RuntimeError, match="ambiguous-executor-route"):
        coordinator.run(
            InventoryAgent(),
            low_stock_context(),
            identity_verified=True,
        )

    assert first.tasks == []
    assert second.tasks == []
    receipts = receipt_store.read_all()
    assert len(receipts) == 1
    assert receipts[0].details["reason"] == "ambiguous-executor-route"
    assert receipts[0].details["matches"] == ["TaskExecutor", "TaskExecutor"]
