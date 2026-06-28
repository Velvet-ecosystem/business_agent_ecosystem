from pathlib import Path

import pytest

from business_agents.agents.change_order_agent import ChangeOrderAgent
from business_agents.capability_registry import capability_for_identity
from business_agents.change_orders import ChangeOrderStore
from business_agents.executors.amendment_record_executor import AmendmentRecordExecutor
from business_agents.gateway.change_order_safety_gate import ChangeOrderSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JsonlJobStore


def context(version="1", record_id="CO-1"):
    return {
        "change_order_id": record_id,
        "job_id": "J-1",
        "version": version,
        "reason": "Customer requested revision",
        "scope_delta": "Add revised installation step",
        "cost_impact_reference": "cost-ref-1",
        "schedule_impact_reference": "schedule-ref-1",
        "_principal_id": "owner-1",
    }


def setup(tmp_path: Path):
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("J-1", "Name", "contact", "Original work", "test"))
    records = ChangeOrderStore(tmp_path / "changes.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    return AmendmentRecordExecutor(jobs, records, receipts), jobs, records, receipts


def run(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_gate_and_first_version(tmp_path: Path) -> None:
    capability = capability_for_identity("change-order", "record-change-order")
    assert capability is not None

    proposal = ChangeOrderAgent().propose(context())
    assert (proposal.intent.route, proposal.intent.action) == (capability.route, capability.action)
    assert ChangeOrderSafetyGate().evaluate(proposal.intent).passed is True

    executor, jobs, records, receipts = setup(tmp_path)
    result = run(executor, proposal.intent)
    receipt = receipts.read_all()[-1]

    assert result.output["version"] == 1
    assert result.receipt_id == receipt.receipt_id
    assert records.latest_for_job("J-1").change_order_id == "CO-1"
    assert jobs.require("J-1").request == "Original work"
    assert receipt.details["record_id"] == "CO-1"


def test_versions_must_be_sequential(tmp_path: Path) -> None:
    executor, _, records, _ = setup(tmp_path)
    run(executor, ChangeOrderAgent().propose(context()).intent)
    with pytest.raises(ValueError, match="change order version must be 2"):
        run(executor, ChangeOrderAgent().propose(context("3", "CO-3")).intent)
    assert records.latest_for_job("J-1").version == 1
