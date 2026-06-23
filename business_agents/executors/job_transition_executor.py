"""Executor for approved job lifecycle transitions."""

from __future__ import annotations

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore


class JobTransitionExecutor(BaseExecutor):
    route = "job-transition"
    allowed_actions = frozenset({"transition-job"})

    def __init__(self, job_store: JsonlJobStore, receipt_store: JsonlReceiptStore) -> None:
        self.job_store = job_store
        self.receipt_store = receipt_store

    def execute(
        self,
        intent: BusinessIntent,
        *,
        authorization_id: str,
        authorization_fingerprint: str,
        authorization_issued_at: float,
        authorization_expires_at: float,
    ) -> ExecutorResult:
        if not self.supports(intent):
            raise ValueError("unsupported intent")
        if not authorization_id.strip() or not authorization_fingerprint.strip():
            raise ValueError("authorization metadata is required")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")

        current = self.job_store.require(intent.subject_id)
        declared_current = JobStatus(str(intent.parameters["current_status"]))
        target = JobStatus(str(intent.parameters["target_status"]))
        if current.status is not declared_current:
            raise ValueError("job status changed before authorized transition")

        updated = self.job_store.transition(current.job_id, target)
        receipt = self.receipt_store.append(
            actor="Job Transition Executor",
            decision="completed",
            executor="Job Transition Executor",
            subject_id=updated.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "job_id": updated.job_id,
                "from_status": current.status.value,
                "to_status": updated.status.value,
                "reason": str(intent.parameters["reason"]),
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Job Transition Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "job_id": updated.job_id,
                "from_status": current.status.value,
                "to_status": updated.status.value,
            },
        )
