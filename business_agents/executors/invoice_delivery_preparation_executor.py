"""Executor for strongly approved local invoice delivery preparation."""

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_delivery_preparations import InvoiceDeliveryPreparation, InvoiceDeliveryPreparationStore
from business_agents.invoice_finalizations import InvoiceFinalizationStore
from business_agents.jobs import JobStatus, JsonlJobStore


class InvoiceDeliveryPreparationExecutor(BaseExecutor):
    route = "invoice-delivery-preparation"
    allowed_actions = frozenset({"prepare-invoice-delivery"})

    def __init__(self, job_store: JsonlJobStore, finalization_store: InvoiceFinalizationStore, preparation_store: InvoiceDeliveryPreparationStore, receipt_store: JsonlReceiptStore) -> None:
        self.job_store = job_store
        self.finalization_store = finalization_store
        self.preparation_store = preparation_store
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
        finalization_id = str(intent.parameters["finalization_id"])
        finalization = self.finalization_store.get(finalization_id)
        if finalization is None:
            raise ValueError("invoice finalization not found")
        if finalization.job_id != job.job_id:
            raise ValueError("invoice finalization belongs to a different job")
        if finalization.invoice_id != str(intent.parameters["invoice_id"]):
            raise ValueError("invoice id does not match finalization")
        record = InvoiceDeliveryPreparation(
            preparation_id=str(intent.parameters["preparation_id"]),
            finalization_id=finalization.finalization_id,
            invoice_id=finalization.invoice_id,
            job_id=job.job_id,
            prepared_by=str(intent.parameters["prepared_by"]),
        )
        self.preparation_store.create(record)
        receipt = self.receipt_store.append(
            actor="Invoice Delivery Preparation Executor",
            decision="completed",
            executor="Invoice Delivery Preparation Executor",
            subject_id=job.job_id,
            details={
                "preparation_id": record.preparation_id,
                "finalization_id": record.finalization_id,
                "invoice_id": record.invoice_id,
                "job_id": record.job_id,
                "prepared_by": record.prepared_by,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Invoice Delivery Preparation Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"preparation_id": record.preparation_id, "invoice_id": record.invoice_id, "job_id": record.job_id},
        )
