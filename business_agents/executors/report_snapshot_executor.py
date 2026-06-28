"""Executor for approved derived report snapshots."""

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.report_snapshots import ReportSnapshot, ReportSnapshotStore


class ReportSnapshotExecutor(BaseExecutor):
    route = "report-snapshot"
    allowed_actions = frozenset({"record-report-snapshot"})

    def __init__(self, snapshots: ReportSnapshotStore, receipts: JsonlReceiptStore) -> None:
        self.snapshots = snapshots
        self.receipts = receipts

    def execute(self, intent: BusinessIntent, *, authorization_id: str, authorization_fingerprint: str, authorization_issued_at: float, authorization_expires_at: float) -> ExecutorResult:
        if not self.supports(intent):
            raise ValueError("unsupported intent")
        if not authorization_id.strip() or not authorization_fingerprint.strip():
            raise ValueError("authorization metadata is required")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")

        snapshot = ReportSnapshot(
            report_id=str(intent.parameters["report_id"]),
            report_type=str(intent.parameters["report_type"]),
            scope_reference=str(intent.parameters["scope_reference"]),
            source_reference=str(intent.parameters["source_reference"]),
            generated_by=str(intent.parameters["generated_by"]),
            generated_at_reference=str(intent.parameters["generated_at_reference"]),
        )
        self.snapshots.create(snapshot)
        receipt = self.receipts.append(
            actor="Report Snapshot Executor",
            decision="completed",
            executor="Report Snapshot Executor",
            subject_id=snapshot.scope_reference,
            details={
                "report_id": snapshot.report_id,
                "report_type": snapshot.report_type,
                "scope_reference": snapshot.scope_reference,
                "source_reference": snapshot.source_reference,
                "generated_by": snapshot.generated_by,
                "source_records_changed": False,
                "external_action_taken": False,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        return ExecutorResult(
            executor_name="Report Snapshot Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"report_id": snapshot.report_id, "source_records_changed": False},
        )
