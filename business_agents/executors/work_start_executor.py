"""Executor for strongly approved work-start ceremonies."""

from __future__ import annotations

from business_agents.booking_records import JsonlBookingStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.work_start import JsonlWorkStartStore, WorkStartRecord


class WorkStartExecutor(BaseExecutor):
    route = "work-start"
    allowed_actions = frozenset({"start-work"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        booking_store: JsonlBookingStore,
        start_store: JsonlWorkStartStore,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.job_store = job_store
        self.booking_store = booking_store
        self.start_store = start_store
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
        if job.status is not JobStatus.SCHEDULED:
            raise ValueError("job status changed before work start")

        booking_id = str(intent.parameters["booking_id"])
        booking = self.booking_store.get(booking_id)
        if booking is None:
            raise ValueError("booking record not found")
        if booking.job_id != job.job_id:
            raise ValueError("booking record belongs to a different job")

        record = WorkStartRecord(
            start_id=str(intent.parameters["start_id"]),
            job_id=job.job_id,
            booking_id=booking.booking_id,
            started_by=str(intent.parameters["started_by"]),
            reason=str(intent.parameters["reason"]),
        )
        self.start_store.create(record)
        updated = self.job_store.transition(job.job_id, JobStatus.IN_PROGRESS)

        receipt = self.receipt_store.append(
            actor="Work Start Executor",
            decision="completed",
            executor="Work Start Executor",
            subject_id=updated.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "start_id": record.start_id,
                "job_id": record.job_id,
                "booking_id": record.booking_id,
                "started_by": record.started_by,
                "reason": record.reason,
                "from_status": job.status.value,
                "to_status": updated.status.value,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Work Start Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "start_id": record.start_id,
                "job_id": record.job_id,
                "booking_id": record.booking_id,
                "started_by": record.started_by,
                "from_status": job.status.value,
                "to_status": updated.status.value,
            },
        )
