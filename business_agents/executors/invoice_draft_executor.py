"""Executor for strongly approved local invoice drafts."""

from business_agents.completion_evidence import CompletionEvidenceStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.invoice_drafts import InvoiceDraft
from business_agents.estimates import money
from business_agents.jobs import JobStatus, JsonlJobStore


class InvoiceDraftExecutor(BaseExecutor):
    route = "invoice-draft"
    allowed_actions = frozenset({"create-invoice-draft"})

    def __init__(self, job_store: JsonlJobStore, evidence_store: CompletionEvidenceStore, invoice_store: JsonlInvoiceDraftStore, receipt_store: JsonlReceiptStore) -> None:
        self.job_store = job_store
        self.evidence_store = evidence_store
        self.invoice_store = invoice_store
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
            raise ValueError("job status changed before invoice drafting")
        evidence_id = str(intent.parameters["evidence_id"])
        evidence = self.evidence_store.get(evidence_id)
        if evidence is None:
            raise ValueError("completion evidence not found")
        if evidence.job_id != job.job_id:
            raise ValueError("completion evidence belongs to a different job")
        draft = InvoiceDraft(
            invoice_id=str(intent.parameters["invoice_id"]),
            job_id=job.job_id,
            evidence_id=evidence.evidence_id,
            currency=str(intent.parameters["currency"]),
            subtotal=money(intent.parameters["subtotal"]),
            tax_amount=money(intent.parameters["tax_amount"]),
            total=money(intent.parameters["total"]),
            notes=str(intent.parameters["notes"]),
        )
        self.invoice_store.create(draft)
        receipt = self.receipt_store.append(
            actor="Invoice Draft Executor",
            decision="completed",
            executor="Invoice Draft Executor",
            subject_id=job.job_id,
            details={
                "invoice_id": draft.invoice_id,
                "job_id": draft.job_id,
                "evidence_id": draft.evidence_id,
                "currency": draft.currency,
                "total": str(draft.total),
                "draft_only": True,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Invoice Draft Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"invoice_id": draft.invoice_id, "job_id": draft.job_id, "total": str(draft.total), "draft_only": True},
        )
