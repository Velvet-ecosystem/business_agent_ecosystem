"""Tests for durable job records and their bounded creation flow."""

from pathlib import Path

import pytest

from business_agents.agents.job_agent import JobAgent
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.executors.job_executor import JobExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.job_safety_gate import JobRecordSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def job_context() -> dict[str, str]:
    return {
        "job_id": "JOB-0001",
        "customer_name": "Alex Morgan",
        "contact": "alex@example.com",
        "request": "Install a Velvet system in a 2008 Hyundai Tiburon.",
        "source": "website-form",
        "intake_task_id": "task_0001",
    }


def test_job_record_starts_in_intake_review() -> None:
    record = JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
    )

    assert record.status is JobStatus.INTAKE_REVIEW


def test_job_lifecycle_allows_only_explicit_transitions() -> None:
    record = JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
    )

    approved = record.transition(JobStatus.APPROVED)

    assert approved.status is JobStatus.APPROVED
    with pytest.raises(ValueError, match="invalid job transition"):
        record.transition(JobStatus.COMPLETED)


def test_completed_and_cancelled_jobs_are_terminal() -> None:
    completed = JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
        status=JobStatus.COMPLETED,
    )

    with pytest.raises(ValueError, match="invalid job transition"):
        completed.transition(JobStatus.IN_PROGRESS)


def test_job_store_reconstructs_current_state(tmp_path: Path) -> None:
    store = JsonlJobStore(tmp_path / "jobs.jsonl")
    store.create(
        JobRecord(
            job_id="JOB-0001",
            customer_name="Alex Morgan",
            contact="alex@example.com",
            request="Install Velvet.",
            source="website-form",
        )
    )
    store.transition("JOB-0001", JobStatus.APPROVED)
    store.transition("JOB-0001", JobStatus.ESTIMATING)

    assert store.require("JOB-0001").status is JobStatus.ESTIMATING
    assert len(store.list_current()) == 1


def test_job_store_rejects_duplicate_job_id(tmp_path: Path) -> None:
    store = JsonlJobStore(tmp_path / "jobs.jsonl")
    record = JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
    )
    store.create(record)

    with pytest.raises(ValueError, match="job already exists"):
        store.create(record)


def test_job_agent_requests_human_approval() -> None:
    proposal = JobAgent().propose(job_context())

    assert proposal.intent.route == "job-record"
    assert proposal.intent.action == "create-job"
    assert proposal.intent.risk_level is RiskLevel.MEDIUM
    assert proposal.intent.approval_mode is ApprovalMode.HUMAN
    assert proposal.authority_granted is False


def test_job_safety_gate_rejects_commercial_fields() -> None:
    proposal = JobAgent().propose(job_context())
    unsafe = type(proposal.intent)(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "quote_total": 5000},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )

    decision = JobRecordSafetyGate().evaluate(unsafe)

    assert decision.passed is False
    assert decision.reason == "commercial-action-fields-forbidden"


def test_approved_job_creation_is_durable_and_receipted(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    job_store = JsonlJobStore(tmp_path / "jobs.jsonl")
    executor = JobExecutor(job_store, receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=JobRecordSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )

    result = coordinator.run(
        JobAgent(),
        job_context(),
        identity_verified=True,
    )

    assert result.status == "completed"
    assert result.output == {"job_id": "JOB-0001", "status": "intake-review"}
    stored = job_store.require("JOB-0001")
    assert stored.metadata["intake_task_id"] == "task_0001"
    assert result.receipt_id


def test_missing_intake_task_cannot_create_job() -> None:
    context = job_context()
    context["intake_task_id"] = ""

    with pytest.raises(ValueError, match="intake_task_id"):
        JobAgent().propose(context)
