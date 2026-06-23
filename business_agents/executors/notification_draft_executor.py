"""Executor for internal booking-confirmation email drafts."""

from __future__ import annotations

from business_agents.booking_records import JsonlBookingStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.notifications import JsonlNotificationDraftStore, NotificationDraft


class NotificationDraftExecutor(BaseExecutor):
    route = "notification-draft"
    allowed_actions = frozenset({"create-booking-confirmation-draft"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        booking_store: JsonlBookingStore,
        draft_store: JsonlNotificationDraftStore,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.job_store = job_store
        self.booking_store = booking_store
        self.draft_store = draft_store
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
            raise ValueError("job status changed before notification drafting")

        booking_id = str(intent.parameters["booking_id"])
        booking = self.booking_store.get(booking_id)
        if booking is None:
            raise ValueError("booking record not found")
        if booking.job_id != job.job_id:
            raise ValueError("booking record belongs to a different job")

        subject = f"Booking confirmation for job {job.job_id}"
        body = (
            f"Hello {job.customer_name},\n\n"
            f"Your booking for {job.request} is scheduled from "
            f"{booking.start.isoformat()} to {booking.end.isoformat()} "
            f"({booking.timezone}).\n\n"
            f"Reference: {booking.event_id}\n\n"
            "This is a prepared confirmation draft and has not been sent."
        )
        draft = NotificationDraft(
            draft_id=str(intent.parameters["draft_id"]),
            job_id=job.job_id,
            booking_id=booking.booking_id,
            channel="email",
            recipient=job.contact,
            subject=subject,
            body=body,
        )
        self.draft_store.create(draft)

        receipt = self.receipt_store.append(
            actor="Notification Draft Executor",
            decision="completed",
            executor="Notification Draft Executor",
            subject_id=job.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "draft_id": draft.draft_id,
                "booking_id": draft.booking_id,
                "job_id": draft.job_id,
                "channel": draft.channel,
                "recipient": draft.recipient,
                "event_id": booking.event_id,
                "sent": False,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Notification Draft Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "draft_id": draft.draft_id,
                "booking_id": draft.booking_id,
                "job_id": draft.job_id,
                "channel": draft.channel,
                "recipient": draft.recipient,
                "sent": False,
            },
        )
