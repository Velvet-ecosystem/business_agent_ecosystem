from pathlib import Path

from business_agents.agents.communication_record_agent import CommunicationRecordAgent
from business_agents.capability_registry import capability_for_identity
from business_agents.communication_records import CommunicationRecordStore
from business_agents.executors.communication_history_executor import CommunicationHistoryExecutor
from business_agents.gateway.communication_history_safety_gate import CommunicationHistorySafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JsonlJobStore


def test_communication_history_end_to_end(tmp_path: Path) -> None:
    capability = capability_for_identity(
        "communication-history",
        "record-communication-reference",
    )
    assert capability is not None

    context = {
        "record_id": "COM-E2E-1",
        "job_id": "JOB-E2E-1",
        "customer_reference": "CUST-E2E-1",
        "channel": "email",
        "direction": "outbound",
        "subject_reference": "subject-ref-e2e",
        "content_reference": "content-ref-e2e",
        "_principal_id": "owner-e2e",
    }

    proposal = CommunicationRecordAgent().propose(context)
    assert proposal.intent.route == capability.route
    assert proposal.intent.action == capability.action

    decision = CommunicationHistorySafetyGate().evaluate(proposal.intent)
    assert decision.passed is True

    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("JOB-E2E-1", "Name", "contact", "Work", "test"))
    records = CommunicationRecordStore(tmp_path / "communications.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    executor = CommunicationHistoryExecutor(jobs, records, receipts)

    result = executor.execute(
        proposal.intent,
        authorization_id="auth-e2e-1",
        authorization_fingerprint="fp-e2e-1",
        authorization_issued_at=1.0,
        authorization_expires_at=2.0,
    )

    stored = records.get("COM-E2E-1")
    receipt = receipts.read_all()[-1]
    assert stored is not None
    assert stored.job_id == "JOB-E2E-1"
    assert stored.customer_reference == "CUST-E2E-1"
    assert result.status == "completed"
    assert result.receipt_id == receipt.receipt_id
    assert receipt.subject_id == "JOB-E2E-1"
    assert receipt.details["message_sent"] is False
    assert receipt.details["mailbox_changed"] is False
