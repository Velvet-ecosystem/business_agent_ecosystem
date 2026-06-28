from dataclasses import replace
from pathlib import Path

from business_agents.agents.communication_record_agent import CommunicationRecordAgent
from business_agents.capability_registry import capability_for_identity
from business_agents.communication_records import CommunicationRecordStore
from business_agents.gateway.communication_history_safety_gate import CommunicationHistorySafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore


def test_wrong_action_stops_before_storage_or_receipt(tmp_path: Path) -> None:
    context = {
        "record_id": "COM-BLOCK-1",
        "job_id": "JOB-BLOCK-1",
        "customer_reference": "CUST-BLOCK-1",
        "channel": "email",
        "direction": "outbound",
        "subject_reference": "subject-ref-block",
        "content_reference": "content-ref-block",
        "_principal_id": "owner-block",
    }
    proposal = CommunicationRecordAgent().propose(context)
    mismatched = replace(proposal.intent, action="record-report-snapshot")

    assert capability_for_identity(mismatched.route, mismatched.action) is None
    decision = CommunicationHistorySafetyGate().evaluate(mismatched)
    assert decision.passed is False

    records_path = tmp_path / "communications.jsonl"
    receipts_path = tmp_path / "receipts.jsonl"
    records = CommunicationRecordStore(records_path)
    receipts = JsonlReceiptStore(receipts_path)

    assert records.get("COM-BLOCK-1") is None
    assert receipts.read_all() == []
