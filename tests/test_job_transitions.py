"""Tests for authority-gated job lifecycle transitions."""

from pathlib import Path

import pytest

from business_agents.agents.job_transition_agent import JobTransitionAgent
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.executors.job_transition_executor import JobTransitionExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.job_transition_safety_gate import JobTransitionSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def seed_job(store: JsonlJobStore, status: JobStatus = JobStatus.APPROVED) -> None:
    store.create(
        JobRecord(
            job_id="JOB-0001",
            customer_name="Alex Morgan",
            contact="alex@example.com",
            request="Install Velvet.",
            source="website-form",
            status=status,
        )
    )


def transition_context(current: str = "approved", target: str = "estimating") -> dict[str, str]:
    return {
        "job_id": "JOB-0001",
        "current_status": current,
        "target_status": target,
        "reason": "The intake review was approved for estimating.",
    }


def test_normal_transition_requires_human_approval() -> None:
    proposal = JobTransitionAgent().propose(transition_context())

    assert proposal.intent.risk_level is RiskLevel.MEDIUM
    assert proposal.intent.approval_mode is ApprovalMode.HUMAN


def test_terminal_transition_requires_strong_human_approval() -> None:
    proposal = JobTransitionAgent().propose(
        transition_context(current="in-progress", target="completed")
    )

    assert proposal.intent.risk_level is RiskLevel.HIGH
    assert proposal.intent.approval_mode is ApprovalMode.STRONG_HUMAN


def test_safety_gate_rejects_skipped_state() -> None:
    proposal = JobTransitionAgent().propose(
        transition_context(current="approved", target="scheduled")
    )

    decision = JobTransitionSafetyGate().evaluate(proposal.intent)

    assert decision.passed is False
    assert decision.reason == "invalid-job-transition"


def test_safety_gate_rejects_extra_fields() -> None:
    proposal = JobTransitionAgent().propose(transition_context())
    intent_type = type(proposal.intent)
    altered = intent_type(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "extra": "not allowed"},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )

    decision = JobTransitionSafetyGate().evaluate(altered)

    assert decision.passed is False
    assert decision.reason == "unexpected-transition-fields"


def test_authorized_transition_updates_store_and_writes_receipt(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    job_store = JsonlJobStore(tmp_path / "jobs.jsonl")
    seed_job(job_store)
    executor = JobTransitionExecutor(job_store, receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=JobTransitionSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )

    result = coordinator.run(
        JobTransitionAgent(),
        transition_context(),
        identity_verified=True,
    )

    assert result.status == "completed"
    assert result.output == {
        "job_id": "JOB-0001",
        "from_status": "approved",
        "to_status": "estimating",
    }
    assert job_store.require("JOB-0001").status is JobStatus.ESTIMATING
    assert result.receipt_id


def test_stale_declared_status_is_rejected_at_execution(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    job_store = JsonlJobStore(tmp_path / "jobs.jsonl")
    seed_job(job_store, JobStatus.ESTIMATING)
    executor = JobTransitionExecutor(job_store, receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=JobTransitionSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )

    with pytest.raises(ValueError, match="status changed"):
        coordinator.run(
            JobTransitionAgent(),
            transition_context(current="approved", target="estimating"),
            identity_verified=True,
        )


def test_invalid_status_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported job status"):
        JobTransitionAgent().propose(
            transition_context(target="finished-ish")
        )
