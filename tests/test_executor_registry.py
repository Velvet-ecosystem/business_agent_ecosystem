from pathlib import Path

import pytest

from business_agents.contracts import BusinessIntent
from business_agents.executors.registry import ExecutorRegistry
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore


def make_task_executor(tmp_path: Path) -> TaskExecutor:
    return TaskExecutor(JsonlReceiptStore(tmp_path / "receipts.jsonl"))


def test_registry_resolves_supported_route_and_action(tmp_path: Path) -> None:
    executor = make_task_executor(tmp_path)
    registry = ExecutorRegistry([executor])
    intent = BusinessIntent(
        route="internal-task",
        action="create-restock-review",
        subject_id="small-workshop",
        parameters={"sku": "FILTER-001", "suggested_quantity": 12},
    )

    assert registry.resolve(intent) is executor
    assert registry.routes == ("internal-task",)


def test_registry_rejects_duplicate_routes(tmp_path: Path) -> None:
    first = make_task_executor(tmp_path)
    second = make_task_executor(tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        ExecutorRegistry([first, second])


def test_registry_rejects_unknown_route() -> None:
    registry = ExecutorRegistry()
    intent = BusinessIntent(
        route="unknown",
        action="do-something",
        subject_id="small-workshop",
        parameters={},
    )

    with pytest.raises(LookupError, match="no executor registered"):
        registry.resolve(intent)


def test_registry_rejects_unsupported_action(tmp_path: Path) -> None:
    registry = ExecutorRegistry([make_task_executor(tmp_path)])
    intent = BusinessIntent(
        route="internal-task",
        action="place-order",
        subject_id="small-workshop",
        parameters={},
    )

    with pytest.raises(LookupError, match="does not support action"):
        registry.resolve(intent)
