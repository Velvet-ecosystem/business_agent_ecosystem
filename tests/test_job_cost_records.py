from pathlib import Path

import pytest

from business_agents.agents.job_cost_record_agent import JobCostRecordAgent
from business_agents.executors.job_reference_executor import JobReferenceExecutor
from business_agents.gateway.job_evidence_safety_gate import JobEvidenceSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.job_cost_records import JobCostRecordStore
from business_agents.jobs import JobRecord, JsonlJobStore


def context(record_id="R-1"):
    return {
        "record_id": record_id,
        "job_id": "J-1",
        "category": "materials",
        "description": "Fasteners and cable",
        "amount_reference": "amount-ref-1",
        "evidence_reference": "evidence-ref-1",
        "_principal_id": "owner-1",
    }


def build(tmp_path: Path):
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("J-1", "Name", "contact", "Work", "test"))
    records = JobCostRecordStore(tmp_path / "records.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    return JobReferenceExecutor(jobs, records, receipts), records, receipts


def run(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_gate_and_record(tmp_path: Path) -> None:
    proposal = JobCostRecordAgent().propose(context())
    assert JobEvidenceSafetyGate().evaluate(proposal.intent).passed is True
    executor, records, receipts = build(tmp_path)
    result = run(executor, proposal.intent)
    assert records.get("R-1").job_id == "J-1"
    assert receipts.read_all()[-1].details["record_id"] == "R-1"
    assert result.output["record_id"] == "R-1"


def test_duplicate_record_id_fails(tmp_path: Path) -> None:
    executor, records, _ = build(tmp_path)
    run(executor, JobCostRecordAgent().propose(context()).intent)
    with pytest.raises(ValueError):
        run(executor, JobCostRecordAgent().propose(context()).intent)
    assert records.get("R-1") is not None
