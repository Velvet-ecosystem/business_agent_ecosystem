"""Executor for strongly approved invoice finalization."""

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.invoice_finalizations import InvoiceFinalization, InvoiceFinalizationStore
from business_agents.jobs import JobStatus, JsonlJobStore


class InvoiceFinalizationExecutor(BaseExecutor):
    route = "invoice-finalization"
    allowed_actions = frozenset({"finalize-invoice"})

    def __init__(self, job_store: JsonlJobStore, invoice_store: JsonlInvoiceDraftStore, finalization_store: InvoiceFinalizationStore, receipt_store: JsonlReceiptStore) -> None:
        self.job_store = job_store
        self.invoice_store = invoice_store
        self.finalization_store = finalization_store
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
        invoice_id = str(intent.parameters["invoice_id"])
        draft = self.invoice_store.get(invoice_id)
        if draft is None:
            raise ValueError("invoice draft not found")
        if draft.job_id != job.job_id:
            raise ValueError("invoice draft belongs to a different job")
        record = InvoiceFinalization(
            finalization_id=str(intent.parameters["finalization_id"]),
            invoice_id=draft.invoice_id,
            job_id=job.job_id,
            approved_by=str(intent.parameters["approved_by"]),
        )
        self.finalization_store.create(record)
        receipt = self.receipt_store.append(
            actor="Invoice Finalization Executor",
            decision="completed",
            executor="Invoice Finalization Executor",
            subject_id=job.job_id,
            details={
                "finalization_id": record.finalization_id,
                "invoice_id": record.invoice_id,
                "job_id": record.job_id,
                "approved_by": record.approved_by,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Invoice Finalization Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"finalization_id": record.finalization_id, "invoice_id": record.invoice_id, "job_id": record.job_id},
        )
