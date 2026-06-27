from pathlib import Path

import pytest

from business_agents.agents.job_completion_agent import JobCompletionAgent
from business_agents.completion_evidence import CompletionEvidence, CompletionEvidenceStore
from business_agents.executors.job_completion_executor import JobCompletionExecutor
from business_agents.gateway.job_completion_safety_gate import JobCompletionSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def make_job(job_id: str = "JOB-1") -> JobRecord:
    return JobRecord(
        job_id=job_id,
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install system",
        source="test",
        status=JobStatus.IN_PROGRESS,
    )


def make_evidence(job_id: str = "JOB-1", evidence_id: str = "EVID-1") -> CompletionEvidence:
    return CompletionEvidence(
        evidence_id=evidence_id,
        job_id=job_id,
        completed_by="owner-1",
        summary="Work complete and verified.",
        checklist=("Power test passed",),
    )


def execute(executor: JobCompletionExecutor, intent):
    return executor.execute(
        intent,
        authorization_id="auth-1",
        authorization_fingerprint="fingerprint-1",
        authorization_issued_at=1.0,
        authorization_expires_at=2.0,
    )


def test_agent_and_gate_require_exact_evidence_reference() -> None:
    proposal = JobCompletionAgent().propose({
        "job_id": "JOB-1",
        "job_status": "in-progress",
        "evidence_id": "EVID-1",
    })
    decision = JobCompletionSafetyGate().evaluate(proposal.intent)
    assert decision.passed is True
    assert proposal.intent.parameters["evidence_id"] == "EVID-1"


def test_completion_requires_existing_exact_evidence(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    evidence = CompletionEvidenceStore(tmp_path / "evidence.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs.create(make_job())
    executor = JobCompletionExecutor(jobs, evidence, receipts)
    intent = JobCompletionAgent().propose({
        "job_id": "JOB-1",
        "job_status": "in-progress",
        "evidence_id": "EVID-1",
    }).intent

    with pytest.raises(ValueError, match="completion evidence not found"):
        execute(executor, intent)
    assert jobs.require("JOB-1").status is JobStatus.IN_PROGRESS


def test_completion_rejects_evidence_bound_to_another_job(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    evidence = CompletionEvidenceStore(tmp_path / "evidence.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs.create(make_job())
    evidence.create(make_evidence(job_id="JOB-2"))
    executor = JobCompletionExecutor(jobs, evidence, receipts)
    intent = JobCompletionAgent().propose({
        "job_id": "JOB-1",
        "job_status": "in-progress",
        "evidence_id": "EVID-1",
    }).intent

    with pytest.raises(ValueError, match="different job"):
        execute(executor, intent)
    assert jobs.require("JOB-1").status is JobStatus.IN_PROGRESS


def test_exact_evidence_allows_receipted_terminal_transition(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    evidence = CompletionEvidenceStore(tmp_path / "evidence.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs.create(make_job())
    evidence.create(make_evidence())
    executor = JobCompletionExecutor(jobs, evidence, receipts)
    intent = JobCompletionAgent().propose({
        "job_id": "JOB-1",
        "job_status": "in-progress",
        "evidence_id": "EVID-1",
    }).intent

    result = execute(executor, intent)

    assert jobs.require("JOB-1").status is JobStatus.COMPLETED
    assert result.output["evidence_id"] == "EVID-1"
    assert result.output["to_status"] == "completed"
    stored_receipts = receipts.read_all()
    assert stored_receipts[-1].details["evidence_id"] == "EVID-1"
