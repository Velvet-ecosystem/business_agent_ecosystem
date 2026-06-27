"""Executor that stores an approved reported amount against an existing invoice."""

from business_agents.amount_reconciliation import reconcile
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.estimates import money
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.invoice_handoff_confirmations import InvoiceHandoffConfirmationStore
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.payment_records import PaymentRecord, PaymentRecordStore


class ReportedAmountRecordingExecutor(BaseExecutor):
    route = "payment-recording"
    allowed_actions = frozenset({"record-reported-payment"})

    def __init__(self, job_store: JsonlJobStore, invoice_store: JsonlInvoiceDraftStore, handoff_store: InvoiceHandoffConfirmationStore, record_store: PaymentRecordStore, receipt_store: JsonlReceiptStore) -> None:
        self.job_store = job_store
        self.invoice_store = invoice_store
        self.handoff_store = handoff_store
        self.record_store = record_store
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

        invoice = self.invoice_store.get(str(intent.parameters["invoice_id"]))
        if invoice is None or invoice.job_id != job.job_id:
            raise ValueError("matching invoice not found")

        handoff = self.handoff_store.get(str(intent.parameters["handoff_confirmation_id"]))
        if handoff is None or handoff.job_id != job.job_id or handoff.invoice_id != invoice.invoice_id:
            raise ValueError("matching handoff confirmation not found")

        currency = str(intent.parameters["currency"])
        if currency != invoice.currency:
            raise ValueError("currency does not match invoice")

        amount = money(intent.parameters["amount"])
        totals = reconcile(invoice.total, self.record_store.total_for_invoice(invoice.invoice_id), amount)
        record = PaymentRecord(
            payment_id=str(intent.parameters["payment_id"]),
            invoice_id=invoice.invoice_id,
            job_id=job.job_id,
            handoff_confirmation_id=handoff.confirmation_id,
            amount=amount,
            currency=currency,
            source_reference=str(intent.parameters["source_reference"]),
            recorded_by=str(intent.parameters["recorded_by"]),
        )
        self.record_store.create(record)

        receipt = self.receipt_store.append(
            actor="Reported Amount Recording Executor",
            decision="completed",
            executor="Reported Amount Recording Executor",
            subject_id=job.job_id,
            details={
                "record_id": record.payment_id,
                "invoice_id": record.invoice_id,
                "recorded_total": str(totals.recorded_total),
                "remaining": str(totals.remaining),
                "state": totals.state,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Reported Amount Recording Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "record_id": record.payment_id,
                "invoice_id": record.invoice_id,
                "recorded_total": str(totals.recorded_total),
                "remaining": str(totals.remaining),
                "state": totals.state,
            },
        )
