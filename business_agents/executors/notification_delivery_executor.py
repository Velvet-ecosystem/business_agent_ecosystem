"""Executor for strongly approved notification delivery."""

from __future__ import annotations

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.delivery_adapter import DeliveryAdapter, DeliveryRequest
from business_agents.delivery_records import DeliveryRecord, JsonlDeliveryStore
from business_agents.executors.base_executor import BaseExecutor
from business_agents.external_operations import ExternalOperationJournal
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.notifications import JsonlNotificationDraftStore


class NotificationDeliveryExecutor(BaseExecutor):
    route = "notification-delivery"
    allowed_actions = frozenset({"deliver-notification-draft"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        draft_store: JsonlNotificationDraftStore,
        delivery_store: JsonlDeliveryStore,
        delivery_adapter: DeliveryAdapter,
        receipt_store: JsonlReceiptStore,
        operation_journal: ExternalOperationJournal | None = None,
    ) -> None:
        self.job_store = job_store
        self.draft_store = draft_store
        self.delivery_store = delivery_store
        self.delivery_adapter = delivery_adapter
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
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")

        job = self.job_store.require(intent.subject_id)
        if job.status is not JobStatus.SCHEDULED:
            raise ValueError("job status changed before notification delivery")

        draft_id = str(intent.parameters["draft_id"])
        draft = self.draft_store.get(draft_id)
        if draft is None:
            raise ValueError("notification draft not found")
        if draft.job_id != job.job_id:
            raise ValueError("notification draft belongs to a different job")

        key = str(intent.parameters["idempotency_key"])
        operation_id = f"delivery:{key}"
        if self.operation_journal is not None:
            self.operation_journal.prepare(
                operation_id=operation_id,
                provider="notification-delivery",
                subject_id=job.job_id,
                idempotency_key=key,
                metadata={"draft_id": draft.draft_id},
            )

        existing = self.delivery_store.get_by_idempotency_key(key)
        sent_now = False
        if existing is not None:
            if existing.job_id != job.job_id or existing.draft_id != draft.draft_id:
                raise ValueError("idempotency key is bound to another delivery")
            record = existing
        else:
            try:
                result = self.delivery_adapter.deliver(
                    DeliveryRequest(
                        idempotency_key=key,
                        recipient=draft.recipient,
                        subject=draft.subject,
                        body=draft.body,
                    )
                )
            except Exception as exc:
                if self.operation_journal is not None:
                    self.operation_journal.failed(operation_id, error=f"{type(exc).__name__}: {exc}")
                raise
            if self.operation_journal is not None:
                self.operation_journal.provider_confirmed(
                    operation_id,
                    external_id=result.provider_message_id,
                )
            record = DeliveryRecord(
                delivery_id=str(intent.parameters["delivery_id"]),
                draft_id=draft.draft_id,
                job_id=job.job_id,
                idempotency_key=key,
                provider_message_id=result.provider_message_id,
            )
            self.delivery_store.create(record)
            if self.operation_journal is not None:
                self.operation_journal.locally_recorded(
                    operation_id,
                    local_record_id=record.delivery_id,
                )
            sent_now = result.created_now

        if existing is not None and self.operation_journal is not None:
            current = self.operation_journal.get(operation_id)
            if current is not None and current.external_id is None:
                self.operation_journal.provider_confirmed(
                    operation_id,
                    external_id=record.provider_message_id,
                )
            self.operation_journal.locally_recorded(
                operation_id,
                local_record_id=record.delivery_id,
            )

        receipt = self.receipt_store.append(
            actor="Notification Delivery Executor",
            decision="completed",
            executor="Notification Delivery Executor",
            subject_id=job.job_id,
            details={
                "delivery_id": record.delivery_id,
                "draft_id": record.draft_id,
                "provider_message_id": record.provider_message_id,
                "idempotency_key": record.idempotency_key,
                "delivered_now": sent_now,
                "operation_id": operation_id,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Notification Delivery Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "delivery_id": record.delivery_id,
                "draft_id": record.draft_id,
                "provider_message_id": record.provider_message_id,
                "delivered_now": sent_now,
                "operation_id": operation_id,
            },
        )
