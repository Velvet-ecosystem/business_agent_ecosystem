"""Executor for estimate-backed job readiness transitions."""

from __future__ import annotations

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.estimates import JsonlEstimateStore
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore


class EstimateReadinessExecutor(BaseExecutor):
    route = "estimate-readiness"
    allowed_actions = frozenset({"mark-ready-to-schedule"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        estimate_store: JsonlEstimateStore,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.job_store = job_store
        self.estimate_store = estimate_store
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

        job = self.job_store.require(intent.subject_id)
        if job.status is not JobStatus.ESTIMATING:
            raise ValueError("job status changed before readiness transition")

        estimate_id = str(intent.parameters["estimate_id"])
        estimate = self.estimate_store.get(estimate_id)
        if estimate is None:
            raise ValueError("estimate draft not found")
        if estimate.job_id != job.job_id:
            raise ValueError("estimate draft belongs to a different job")

        updated = self.job_store.transition(job.job_id, JobStatus.READY_TO_SCHEDULE)
        receipt = self.receipt_store.append(
            actor="Estimate Readiness Executor",
            decision="completed",
            executor="Estimate Readiness Executor",
            subject_id=updated.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "job_id": updated.job_id,
                "estimate_id": estimate.estimate_id,
                "estimate_total": str(estimate.total),
                "currency": estimate.currency,
                "from_status": job.status.value,
                "to_status": updated.status.value,
                "reason": str(intent.parameters["reason"]),
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Estimate Readiness Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "job_id": updated.job_id,
                "estimate_id": estimate.estimate_id,
                "from_status": job.status.value,
                "to_status": updated.status.value,
            },
        )
