"""Executor for strongly approved invoice handoff confirmation."""

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_delivery_preparations import InvoiceDeliveryPreparationStore
from business_agents.invoice_handoff_confirmations import InvoiceHandoffConfirmation, InvoiceHandoffConfirmationStore
from business_agents.jobs import JobStatus, JsonlJobStore


class InvoiceHandoffConfirmationExecutor(BaseExecutor):
    route = "invoice-handoff-confirmation"
    allowed_actions = frozenset({"confirm-invoice-handoff"})

    def __init__(self, job_store: JsonlJobStore, preparation_store: InvoiceDeliveryPreparationStore, confirmation_store: InvoiceHandoffConfirmationStore, receipt_store: JsonlReceiptStore) -> None:
        self.job_store = job_store
        self.preparation_store = preparation_store
        self.confirmation_store = confirmation_store
        self.receipt_store = receipt_store

    def execute(self, intent: BusinessIntent, *, authorization_id: str, authorization_fingerprint: str, authorization_issued_at: float, authorization_expires_at: float) -> ExecutorResult:
        if not self.supports(intent):
            raise ValueError("unsupported intent")
        if not authorization_id.strip() or not authorization_fingerprint.strip():
            raise ValueError("authorization metadata is required")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")
        job = self.job_store.require(intent.subject_id)
        if job.status is not JobStatus.COMPLETED:
            raise ValueError("job must remain completed")
        preparation = self.preparation_store.get(str(intent.parameters["preparation_id"]))
        if preparation is None:
            raise ValueError("invoice preparation not found")
        if preparation.job_id != job.job_id:
            raise ValueError("invoice preparation belongs to a different job")
        if preparation.invoice_id != str(intent.parameters["invoice_id"]):
            raise ValueError("invoice id does not match preparation")
        record = InvoiceHandoffConfirmation(
            confirmation_id=str(intent.parameters["confirmation_id"]),
            preparation_id=preparation.preparation_id,
            invoice_id=preparation.invoice_id,
            job_id=job.job_id,
            channel_reference=str(intent.parameters["channel_reference"]),
            recipient_reference=str(intent.parameters["recipient_reference"]),
            confirmed_by=str(intent.parameters["confirmed_by"]),
        )
        self.confirmation_store.create(record)
        receipt = self.receipt_store.append(
            actor="Invoice Handoff Confirmation Executor",
            decision="completed",
            executor="Invoice Handoff Confirmation Executor",
            subject_id=job.job_id,
            details={
                "confirmation_id": record.confirmation_id,
                "preparation_id": record.preparation_id,
                "invoice_id": record.invoice_id,
                "job_id": record.job_id,
                "channel_reference": record.channel_reference,
                "recipient_reference": record.recipient_reference,
                "confirmed_by": record.confirmed_by,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Invoice Handoff Confirmation Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"confirmation_id": record.confirmation_id, "invoice_id": record.invoice_id, "job_id": record.job_id},
        )
