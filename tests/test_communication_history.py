from pathlib import Path

import pytest

from business_agents.agents.communication_record_agent import CommunicationRecordAgent
from business_agents.communication_records import CommunicationRecordStore
from business_agents.executors.communication_history_executor import CommunicationHistoryExecutor
from business_agents.gateway.communication_history_safety_gate import CommunicationHistorySafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JsonlJobStore


def context(record_id="COM-1", direction="outbound"):
    return {
        "record_id": record_id,
        "job_id": "JOB-1",
        "customer_reference": "CUST-1",
        "channel": "email",
        "direction": direction,
        "subject_reference": "subject-ref-1",
        "content_reference": "content-ref-1",
        "_principal_id": "owner-1",
    }


def build(tmp_path: Path):
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("JOB-1", "Name", "contact", "Work", "test"))
    records = CommunicationRecordStore(tmp_path / "communications.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    return CommunicationHistoryExecutor(jobs, records, receipts), records, receipts


def run(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_gate_and_archival_record(tmp_path: Path) -> None:
    proposal = CommunicationRecordAgent().propose(context())
    assert CommunicationHistorySafetyGate().evaluate(proposal.intent).passed is True
    executor, records, receipts = build(tmp_path)
    result = run(executor, proposal.intent)
    assert records.get("COM-1").direction == "outbound"
    assert len(records.list_for_job("JOB-1")) == 1
    assert receipts.read_all()[-1].details["message_sent"] is False
    assert receipts.read_all()[-1].details["mailbox_changed"] is False
    assert result.output["message_sent"] is False


def test_invalid_direction_fails_closed() -> None:
    proposal = CommunicationRecordAgent().propose(context(direction="sideways"))
    assert CommunicationHistorySafetyGate().evaluate(proposal.intent).passed is False


def test_duplicate_record_id_fails(tmp_path: Path) -> None:
    executor, records, _ = build(tmp_path)
    run(executor, CommunicationRecordAgent().propose(context()).intent)
    with pytest.raises(ValueError):
        run(executor, CommunicationRecordAgent().propose(context()).intent)
    assert records.get("COM-1") is not None
