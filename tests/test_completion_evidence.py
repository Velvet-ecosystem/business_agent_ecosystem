from pathlib import Path

from business_agents.agents.completion_evidence_agent import CompletionEvidenceAgent
from business_agents.completion_evidence import CompletionEvidenceStore
from business_agents.executors.completion_evidence_executor import CompletionEvidenceExecutor
from business_agents.gateway.completion_evidence_safety_gate import CompletionEvidenceSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def context() -> dict[str, object]:
    return {
        "evidence_id": "EVID-1",
        "job_id": "JOB-1",
        "job_status": "in-progress",
        "_principal_id": "owner-1",
        "summary": "Installation completed and verified.",
        "checklist": ["Power test passed", "Workspace cleaned"],
        "artifact_refs": ["photo:before-after-1"],
        "customer_acknowledged": True,
    }


def test_completion_evidence_round_trip(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("JOB-1", "Alex", "a@example.com", "Install", "manual"))
    jobs.transition("JOB-1", JobStatus.APPROVED)
    jobs.transition("JOB-1", JobStatus.ESTIMATING)
    jobs.transition("JOB-1", JobStatus.READY_TO_SCHEDULE)
    jobs.transition("JOB-1", JobStatus.SCHEDULED)
    jobs.transition("JOB-1", JobStatus.IN_PROGRESS)

    evidence = CompletionEvidenceStore(tmp_path / "completion_evidence.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    proposal = CompletionEvidenceAgent().propose(context())
    assert CompletionEvidenceSafetyGate().evaluate(proposal.intent).passed

    result = CompletionEvidenceExecutor(jobs, evidence, receipts).execute(
        proposal.intent,
        authorization_id="auth-1",
        authorization_fingerprint="fingerprint-1",
        authorization_issued_at=1.0,
        authorization_expires_at=2.0,
    )

    stored = evidence.get_by_job("JOB-1")
    assert stored is not None
    assert stored.completed_by == "owner-1"
    assert stored.customer_acknowledged is True
    assert result.output["evidence_id"] == "EVID-1"


def test_agent_ignores_caller_completed_by() -> None:
    supplied = context()
    supplied["completed_by"] = "forged-user"
    proposal = CompletionEvidenceAgent().propose(supplied)
    assert proposal.intent.parameters["completed_by"] == "owner-1"
