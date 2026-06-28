from pathlib import Path

import pytest

from business_agents.agents.report_snapshot_agent import ReportSnapshotAgent
from business_agents.capability_registry import capability_for_identity
from business_agents.executors.report_snapshot_executor import ReportSnapshotExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.report_snapshot_safety_gate import ReportSnapshotSafetyGate
from business_agents.report_snapshots import ReportSnapshotStore


def context(report_id="REP-1"):
    return {
        "report_id": report_id,
        "report_type": "job-summary",
        "scope_reference": "JOB-1",
        "source_reference": "source-set-1",
        "generated_at_reference": "time-ref-1",
        "_principal_id": "owner-1",
    }


def build(tmp_path: Path):
    snapshots = ReportSnapshotStore(tmp_path / "reports.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    return ReportSnapshotExecutor(snapshots, receipts), snapshots, receipts


def run(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_gate_and_snapshot(tmp_path: Path) -> None:
    capability = capability_for_identity("report-snapshot", "record-report-snapshot")
    assert capability is not None

    proposal = ReportSnapshotAgent().propose(context())
    assert (proposal.intent.route, proposal.intent.action) == (capability.route, capability.action)
    assert ReportSnapshotSafetyGate().evaluate(proposal.intent).passed is True

    executor, snapshots, receipts = build(tmp_path)
    result = run(executor, proposal.intent)
    receipt = receipts.read_all()[-1]

    assert snapshots.get("REP-1").source_reference == "source-set-1"
    assert receipt.details["source_records_changed"] is False
    assert receipt.details["external_action_taken"] is False
    assert result.output["source_records_changed"] is False
    assert result.receipt_id == receipt.receipt_id


def test_duplicate_report_id_fails(tmp_path: Path) -> None:
    executor, snapshots, _ = build(tmp_path)
    run(executor, ReportSnapshotAgent().propose(context()).intent)
    with pytest.raises(ValueError):
        run(executor, ReportSnapshotAgent().propose(context()).intent)
    assert snapshots.get("REP-1") is not None
