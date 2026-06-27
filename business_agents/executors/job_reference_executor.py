"""Executor for approved job reference records."""

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.job_cost_records import JobCostRecord, JobCostRecordStore
from business_agents.jobs import JsonlJobStore


class JobReferenceExecutor(BaseExecutor):
    route = "job-cost-record"
    allowed_actions = frozenset({"record-job-cost-reference"})

    def __init__(self, jobs: JsonlJobStore, records: JobCostRecordStore, receipts: JsonlReceiptStore) -> None:
        self.jobs = jobs
        self.records = records
        self.receipts = receipts

    def execute(self, intent: BusinessIntent, *, authorization_id: str, authorization_fingerprint: str, authorization_issued_at: float, authorization_expires_at: float) -> ExecutorResult:
        job = self.jobs.require(intent.subject_id)
        record = JobCostRecord(
            str(intent.parameters["record_id"]),
            job.job_id,
            str(intent.parameters["category"]),
            str(intent.parameters["description"]),
            str(intent.parameters["amount_reference"]),
            str(intent.parameters["evidence_reference"]),
            str(intent.parameters["recorded_by"]),
        )
        self.records.create(record)
        receipt = self.receipts.append(
            actor="Job Reference Executor",
            decision="completed",
            executor="Job Reference Executor",
            subject_id=job.job_id,
            details={"record_id": record.record_id, "category": record.category, "authorization_id": authorization_id},
        )
        return ExecutorResult(executor_name="Job Reference Executor", status="completed", receipt_id=receipt.receipt_id, output={"record_id": record.record_id, "job_id": record.job_id})
