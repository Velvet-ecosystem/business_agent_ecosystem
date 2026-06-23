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
    allowed_actions = frozenset({"create-restock-review", "create-intake-review"})

    def __init__(self, receipt_store: JsonlReceiptStore) -> None:
        self.receipt_store = receipt_store
        self.tasks: list[InternalTask] = []

    def execute(
        self,
        intent: BusinessIntent,
        *,
        authorization_id: str,
        authorization_fingerprint: str,
        authorization_issued_at: float,
        authorization_expires_at: float,
    ) -> ExecutorResult:
        if not authorization_id.strip():
            raise ValueError("authorization_id is required")
        if not authorization_fingerprint.strip():
            raise ValueError("authorization_fingerprint is required")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")
        if not self.supports(intent):
            raise ValueError("unsupported intent")

        title = self._build_title(intent)
        auth_metadata = {
            "authorization_id": authorization_id,
            "authorization_fingerprint": authorization_fingerprint,
            "authorization_issued_at": authorization_issued_at,
            "authorization_expires_at": authorization_expires_at,
        }
        task = InternalTask(
            task_id=f"task_{len(self.tasks) + 1:04d}",
            title=title,
            subject_id=intent.subject_id,
            metadata={**auth_metadata, **dict(intent.parameters)},
        )

        receipt = self.receipt_store.append(
            actor="Task Executor",
            decision="completed",
            executor="Task Executor",
            subject_id=intent.subject_id,
            details={
                **auth_metadata,
                "route": intent.route,
                "action": intent.action,
                "parameters": dict(intent.parameters),
                "task_id": task.task_id,
                "title": task.title,
            },
        )
        self.tasks.append(task)
        return ExecutorResult(
            executor_name="Task Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"task_id": task.task_id, "title": task.title},
        )

    @staticmethod
    def _build_title(intent: BusinessIntent) -> str:
        if intent.action == "create-restock-review":
            sku = str(intent.parameters["sku"])
            quantity = int(intent.parameters["suggested_quantity"])
            return f"Review restock request for {sku}, quantity {quantity}"
        if intent.action == "create-intake-review":
            customer_name = str(intent.parameters["customer_name"])
            request = str(intent.parameters["request"]).strip().replace("\n", " ")
            summary = request if len(request) <= 80 else request[:77].rstrip() + "..."
            return f"Review customer request from {customer_name}: {summary}"
        raise ValueError("unsupported intent")
