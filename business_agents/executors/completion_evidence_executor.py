"""Executor for approved completion evidence records."""

from __future__ import annotations

from business_agents.completion_evidence import CompletionEvidence, CompletionEvidenceStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore


class CompletionEvidenceExecutor(BaseExecutor):
    route = "completion-evidence"
    allowed_actions = frozenset({"record-completion-evidence"})

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
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")

        job = self.job_store.require(intent.subject_id)
        if job.status is not JobStatus.IN_PROGRESS:
            raise ValueError("job status changed before completion evidence recording")

        record = CompletionEvidence(
            evidence_id=str(intent.parameters["evidence_id"]),
            job_id=job.job_id,
            completed_by=str(intent.parameters["completed_by"]),
            summary=str(intent.parameters["summary"]),
            checklist=tuple(intent.parameters["checklist"]),
            artifact_refs=tuple(intent.parameters["artifact_refs"]),
            customer_acknowledged=bool(intent.parameters["customer_acknowledged"]),
        )
        self.evidence_store.create(record)
        receipt = self.receipt_store.append(
            actor="Completion Evidence Executor",
            decision="completed",
            executor="Completion Evidence Executor",
            subject_id=job.job_id,
            details={
                "evidence_id": record.evidence_id,
                "job_id": record.job_id,
                "completed_by": record.completed_by,
                "checklist_count": len(record.checklist),
                "artifact_count": len(record.artifact_refs),
                "customer_acknowledged": record.customer_acknowledged,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Completion Evidence Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "evidence_id": record.evidence_id,
                "job_id": record.job_id,
                "customer_acknowledged": record.customer_acknowledged,
            },
        )
