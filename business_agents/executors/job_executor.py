"""Executor for approved durable job-record operations."""

from __future__ import annotations

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JsonlJobStore


class JobExecutor(BaseExecutor):
    route = "job-record"
    allowed_actions = frozenset({"create-job"})

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

        record = JobRecord(
            job_id=str(intent.parameters["job_id"]),
            customer_name=str(intent.parameters["customer_name"]),
            contact=str(intent.parameters["contact"]),
            request=str(intent.parameters["request"]),
            source=str(intent.parameters["source"]),
            metadata={
                "intake_task_id": str(intent.parameters["intake_task_id"]),
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        self.job_store.create(record)

        receipt = self.receipt_store.append(
            actor="Job Executor",
            decision="completed",
            executor="Job Executor",
            subject_id=record.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "job_id": record.job_id,
                "status": record.status.value,
                "intake_task_id": record.metadata["intake_task_id"],
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Job Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "job_id": record.job_id,
                "status": record.status.value,
            },
        )
