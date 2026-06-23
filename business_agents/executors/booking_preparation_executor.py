"""Executor for approved exact-window booking preparation."""

from __future__ import annotations

from business_agents.bookings import BookingPreparation, JsonlBookingPreparationStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.schedules import JsonlScheduleStore


class BookingPreparationExecutor(BaseExecutor):
    route = "booking-preparation"
    allowed_actions = frozenset({"prepare-selected-window"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        schedule_store: JsonlScheduleStore,
        preparation_store: JsonlBookingPreparationStore,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.job_store = job_store
        self.schedule_store = schedule_store
        self.preparation_store = preparation_store
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
        if job.status is not JobStatus.READY_TO_SCHEDULE:
            raise ValueError("job status changed before booking preparation")

        proposal_id = str(intent.parameters["proposal_id"])
        proposal = self.schedule_store.get(proposal_id)
        if proposal is None:
            raise ValueError("schedule proposal not found")
        if proposal.job_id != job.job_id:
            raise ValueError("schedule proposal belongs to a different job")

        selected_index = int(intent.parameters["selected_index"])
        if selected_index >= len(proposal.windows):
            raise ValueError("selected schedule window does not exist")
        selected = proposal.windows[selected_index]

        record = BookingPreparation(
            preparation_id=str(intent.parameters["preparation_id"]),
            proposal_id=proposal.proposal_id,
            job_id=job.job_id,
            selected_index=selected_index,
            start=selected.start,
            end=selected.end,
            timezone=proposal.timezone,
            notes=str(intent.parameters.get("notes", "")),
            metadata={
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        self.preparation_store.create(record)

        receipt = self.receipt_store.append(
            actor="Booking Preparation Executor",
            decision="completed",
            executor="Booking Preparation Executor",
            subject_id=job.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "preparation_id": record.preparation_id,
                "proposal_id": record.proposal_id,
                "job_id": record.job_id,
                "selected_index": record.selected_index,
                "start": record.start.isoformat(),
                "end": record.end.isoformat(),
                "timezone": record.timezone,
                "booking_created": False,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Booking Preparation Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "preparation_id": record.preparation_id,
                "proposal_id": record.proposal_id,
                "job_id": record.job_id,
                "selected_index": record.selected_index,
                "start": record.start.isoformat(),
                "end": record.end.isoformat(),
                "booking_created": False,
            },
        )
