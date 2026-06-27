"""Executor for strongly approved terminal job completion."""

from __future__ import annotations

from business_agents.completion_evidence import CompletionEvidenceStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore


class JobCompletionExecutor(BaseExecutor):
    route = "job-completion"
    allowed_actions = frozenset({"complete-job"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        evidence_store: CompletionEvidenceStore,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.job_store = job_store
        self.evidence_store = evidence_store
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
        if job.status is not JobStatus.IN_PROGRESS:
            raise ValueError("job status changed before completion")

        evidence_id = str(intent.parameters["evidence_id"])
        evidence = self.evidence_store.get(evidence_id)
        if evidence is None:
            raise ValueError("completion evidence not found")
        if evidence.job_id != job.job_id:
            raise ValueError("completion evidence belongs to a different job")
        bound = self.evidence_store.get_by_job(job.job_id)
        if bound is None or bound.evidence_id != evidence_id:
            raise ValueError("exact completion evidence is required")

        updated = self.job_store.transition(job.job_id, JobStatus.COMPLETED)
        receipt = self.receipt_store.append(
            actor="Job Completion Executor",
            decision="completed",
            executor="Job Completion Executor",
            subject_id=updated.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "job_id": job.job_id,
                "evidence_id": evidence.evidence_id,
                "completed_by": evidence.completed_by,
                "from_status": job.status.value,
                "to_status": updated.status.value,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Job Completion Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "job_id": updated.job_id,
                "evidence_id": evidence.evidence_id,
                "from_status": job.status.value,
                "to_status": updated.status.value,
            },
        )
