"""Executor for approved append-only amendment records."""

from business_agents.change_orders import ChangeOrder, ChangeOrderStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JsonlJobStore


class AmendmentRecordExecutor(BaseExecutor):
    route = "change-order"
    allowed_actions = frozenset({"record-change-order"})

    def __init__(self, jobs: JsonlJobStore, records: ChangeOrderStore, receipts: JsonlReceiptStore) -> None:
        self.jobs = jobs
        self.records = records
        self.receipts = receipts

    def execute(self, intent: BusinessIntent, *, authorization_id: str, authorization_fingerprint: str, authorization_issued_at: float, authorization_expires_at: float) -> ExecutorResult:
        job = self.jobs.require(intent.subject_id)
        record = ChangeOrder(
            change_order_id=str(intent.parameters["change_order_id"]),
            job_id=job.job_id,
            version=int(intent.parameters["version"]),
            reason=str(intent.parameters["reason"]),
            scope_delta=str(intent.parameters["scope_delta"]),
            cost_impact_reference=str(intent.parameters["cost_impact_reference"]),
            schedule_impact_reference=str(intent.parameters["schedule_impact_reference"]),
            proposed_by=str(intent.parameters["proposed_by"]),
        )
        self.records.create(record)
        receipt = self.receipts.append(
            actor="Amendment Record Executor",
            decision="completed",
            executor="Amendment Record Executor",
            subject_id=job.job_id,
            details={"record_id": record.change_order_id, "version": record.version, "authorization_id": authorization_id},
        )
        return ExecutorResult(executor_name="Amendment Record Executor", status="completed", receipt_id=receipt.receipt_id, output={"record_id": record.change_order_id, "version": record.version})
