"""Executor for strongly approved external calendar bookings."""

from __future__ import annotations

from business_agents.booking_records import BookingRecord, JsonlBookingStore
from business_agents.bookings import JsonlBookingPreparationStore
from business_agents.calendar_adapter import CalendarAdapter, CalendarEventRequest
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.external_operations import ExternalOperationJournal
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore


class BookingExecutor(BaseExecutor):
    route = "calendar-booking"
    allowed_actions = frozenset({"create-calendar-booking"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        preparation_store: JsonlBookingPreparationStore,
        booking_store: JsonlBookingStore,
        calendar_adapter: CalendarAdapter,
        receipt_store: JsonlReceiptStore,
        operation_journal: ExternalOperationJournal | None = None,
    ) -> None:
        self.job_store = job_store
        self.preparation_store = preparation_store
        self.booking_store = booking_store
        self.calendar_adapter = calendar_adapter
        self.receipt_store = receipt_store
        self.operation_journal = operation_journal

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
        if job.status not in {JobStatus.READY_TO_SCHEDULE, JobStatus.SCHEDULED}:
            raise ValueError("job status does not permit booking")

        preparation_id = str(intent.parameters["preparation_id"])
        preparation = self.preparation_store.get(preparation_id)
        if preparation is None:
            raise ValueError("booking preparation not found")
        if preparation.job_id != job.job_id:
            raise ValueError("booking preparation belongs to a different job")

        idempotency_key = str(intent.parameters["idempotency_key"])
        operation_id = f"calendar:{idempotency_key}"
        if self.operation_journal is not None:
            self.operation_journal.prepare(
                operation_id=operation_id,
                provider="calendar",
                subject_id=job.job_id,
                idempotency_key=idempotency_key,
                metadata={"preparation_id": preparation.preparation_id},
            )

        existing = self.booking_store.get_by_idempotency_key(idempotency_key)
        if job.status is JobStatus.SCHEDULED and existing is None:
            raise ValueError("scheduled job cannot create another booking")

        created_now = False
        if existing is not None:
            if existing.job_id != job.job_id or existing.preparation_id != preparation.preparation_id:
                raise ValueError("idempotency key is bound to another booking")
            record = existing
        else:
            event = self.calendar_adapter.create_event(
                CalendarEventRequest(
                    idempotency_key=idempotency_key,
                    title=str(intent.parameters["title"]),
                    start=preparation.start,
                    end=preparation.end,
                    timezone=preparation.timezone,
                    description=str(intent.parameters.get("description", "")),
                )
            )
            if self.operation_journal is not None:
                self.operation_journal.provider_confirmed(
                    operation_id,
                    external_id=event.event_id,
                )
            record = BookingRecord(
                booking_id=str(intent.parameters["booking_id"]),
                job_id=job.job_id,
                preparation_id=preparation.preparation_id,
                idempotency_key=idempotency_key,
                event_id=event.event_id,
                start=preparation.start,
                end=preparation.end,
                timezone=preparation.timezone,
            )
            self.booking_store.create(record)
            if self.operation_journal is not None:
                self.operation_journal.locally_recorded(
                    operation_id,
                    local_record_id=record.booking_id,
                )
            created_now = event.created

        if existing is not None and self.operation_journal is not None:
            current = self.operation_journal.get(operation_id)
            if current is not None and current.external_id is None:
                self.operation_journal.provider_confirmed(
                    operation_id,
                    external_id=record.event_id,
                )
            self.operation_journal.locally_recorded(
                operation_id,
                local_record_id=record.booking_id,
            )

        if job.status is JobStatus.READY_TO_SCHEDULE:
            updated = self.job_store.transition(job.job_id, JobStatus.SCHEDULED)
        else:
            updated = job

        receipt = self.receipt_store.append(
            actor="Booking Executor",
            decision="completed",
            executor="Booking Executor",
            subject_id=updated.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "booking_id": record.booking_id,
                "preparation_id": record.preparation_id,
                "job_id": record.job_id,
                "event_id": record.event_id,
                "idempotency_key": record.idempotency_key,
                "start": record.start.isoformat(),
                "end": record.end.isoformat(),
                "timezone": record.timezone,
                "calendar_event_created_now": created_now,
                "job_status": updated.status.value,
                "operation_id": operation_id,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Booking Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "booking_id": record.booking_id,
                "job_id": record.job_id,
                "event_id": record.event_id,
                "idempotency_key": record.idempotency_key,
                "calendar_event_created_now": created_now,
                "job_status": updated.status.value,
                "operation_id": operation_id,
            },
        )
