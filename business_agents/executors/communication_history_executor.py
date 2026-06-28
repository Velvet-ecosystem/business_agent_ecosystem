"""Executor for approved archival communication records."""

from business_agents.communication_records import CommunicationRecord, CommunicationRecordStore
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JsonlJobStore


class CommunicationHistoryExecutor(BaseExecutor):
    route = "communication-history"
    allowed_actions = frozenset({"record-communication-reference"})

    def __init__(self, jobs: JsonlJobStore, records: CommunicationRecordStore, receipts: JsonlReceiptStore) -> None:
        self.jobs = jobs
        self.records = records
        self.receipts = receipts

    def execute(self, intent: BusinessIntent, *, authorization_id: str, authorization_fingerprint: str, authorization_issued_at: float, authorization_expires_at: float) -> ExecutorResult:
        if not self.supports(intent):
            raise ValueError("unsupported intent")
        if not authorization_id.strip() or not authorization_fingerprint.strip():
            raise ValueError("authorization metadata is required")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")

        job = self.jobs.require(intent.subject_id)
        record = CommunicationRecord(
            record_id=str(intent.parameters["record_id"]),
            job_id=job.job_id,
            customer_reference=str(intent.parameters["customer_reference"]),
            channel=str(intent.parameters["channel"]),
            direction=str(intent.parameters["direction"]),
            subject_reference=str(intent.parameters["subject_reference"]),
            content_reference=str(intent.parameters["content_reference"]),
            recorded_by=str(intent.parameters["recorded_by"]),
        )
        self.records.create(record)
        receipt = self.receipts.append(
            actor="Communication History Executor",
            decision="completed",
            executor="Communication History Executor",
            subject_id=job.job_id,
            details={
                "record_id": record.record_id,
                "job_id": record.job_id,
                "customer_reference": record.customer_reference,
                "channel": record.channel,
                "direction": record.direction,
                "recorded_by": record.recorded_by,
                "message_sent": False,
                "mailbox_changed": False,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        return ExecutorResult(
            executor_name="Communication History Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"record_id": record.record_id, "job_id": record.job_id, "message_sent": False},
        )
