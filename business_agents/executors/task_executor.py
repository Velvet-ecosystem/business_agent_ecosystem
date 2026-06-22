"""Executor for approved internal business tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore


@dataclass(frozen=True)
class InternalTask:
    task_id: str
    title: str
    subject_id: str
    metadata: Mapping[str, Any]


class TaskExecutor(BaseExecutor):
    route = "internal-task"
    allowed_actions = frozenset({"create-restock-review"})

    def __init__(self, receipt_store: JsonlReceiptStore) -> None:
        self.receipt_store = receipt_store
        self.tasks: list[InternalTask] = []

    def execute(self, intent: BusinessIntent, *, authorization_id: str) -> ExecutorResult:
        if not authorization_id.strip():
            raise ValueError("authorization_id is required")
        if not self.supports(intent):
            raise ValueError("unsupported intent")

        sku = str(intent.parameters["sku"])
        quantity = int(intent.parameters["suggested_quantity"])
        task = InternalTask(
            task_id=f"task_{len(self.tasks) + 1:04d}",
            title=f"Review restock request for {sku}, quantity {quantity}",
            subject_id=intent.subject_id,
            metadata={"authorization_id": authorization_id, **dict(intent.parameters)},
        )
        self.tasks.append(task)

        receipt = self.receipt_store.append(
            actor="Task Executor",
            decision="completed",
            executor="Task Executor",
            subject_id=intent.subject_id,
            details={
                "authorization_id": authorization_id,
                "route": intent.route,
                "action": intent.action,
                "parameters": dict(intent.parameters),
                "task_id": task.task_id,
                "title": task.title,
            },
        )
        return ExecutorResult(
            executor_name="Task Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"task_id": task.task_id, "title": task.title},
        )
