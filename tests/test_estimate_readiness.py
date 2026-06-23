"""Tests for estimate-backed transition to ready-to-schedule."""

from pathlib import Path

import pytest

from business_agents.agents.estimate_readiness_agent import EstimateReadinessAgent
from business_agents.estimates import EstimateDraft, JsonlEstimateStore, money
from business_agents.executors.estimate_readiness_executor import EstimateReadinessExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.estimate_readiness_safety_gate import EstimateReadinessSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def readiness_context() -> dict[str, str]:
    return {
        "job_id": "JOB-0001",
        "estimate_id": "EST-0001",
        "current_status": "estimating",
        "reason": "The internal estimate draft is complete and ready for scheduling review.",
    }


def seed_job(store: JsonlJobStore, job_id: str = "JOB-0001") -> None:
    store.create(
        JobRecord(
            job_id=job_id,
            customer_name="Alex Morgan",
            contact="alex@example.com",
            request="Install Velvet.",
            source="website-form",
            status=JobStatus.ESTIMATING,
        )
    )


def seed_estimate(
    store: JsonlEstimateStore,
    estimate_id: str = "EST-0001",
    job_id: str = "JOB-0001",
) -> None:
    store.create(
        EstimateDraft(
            estimate_id=estimate_id,
            job_id=job_id,
            currency="CAD",
            labour_subtotal=money("1200"),
            materials_subtotal=money("2500"),
            contingency_amount=money("370"),
            margin_amount=money("814"),
            tax_amount=money("244.20"),
            total=money("5128.20"),
        )
    )


def build_coordinator(tmp_path: Path):
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    job_store = JsonlJobStore(tmp_path / "jobs.jsonl")
    estimate_store = JsonlEstimateStore(tmp_path / "estimates.jsonl")
    executor = EstimateReadinessExecutor(job_store, estimate_store, receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=EstimateReadinessSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )
    return coordinator, job_store, estimate_store


def test_agent_requires_estimating_status() -> None:
    context = readiness_context()
    context["current_status"] = "approved"

    with pytest.raises(ValueError, match="job must be in estimating status"):
        EstimateReadinessAgent().propose(context)


def test_safety_gate_rejects_unexpected_fields() -> None:
    proposal = EstimateReadinessAgent().propose(readiness_context())
    intent_type = type(proposal.intent)
    altered = intent_type(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "send_quote": True},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )

    decision = EstimateReadinessSafetyGate().evaluate(altered)

    assert decision.passed is False
    assert decision.reason == "unexpected-readiness-fields"


def test_missing_estimate_blocks_transition(tmp_path: Path) -> None:
    coordinator, job_store, _ = build_coordinator(tmp_path)
    seed_job(job_store)

    with pytest.raises(ValueError, match="estimate draft not found"):
        coordinator.run(
            EstimateReadinessAgent(),
            readiness_context(),
            identity_verified=True,
        )

    assert job_store.require("JOB-0001").status is JobStatus.ESTIMATING


def test_estimate_for_different_job_blocks_transition(tmp_path: Path) -> None:
    coordinator, job_store, estimate_store = build_coordinator(tmp_path)
    seed_job(job_store)
    seed_estimate(estimate_store, job_id="JOB-9999")

    with pytest.raises(ValueError, match="different job"):
        coordinator.run(
            EstimateReadinessAgent(),
            readiness_context(),
            identity_verified=True,
        )

    assert job_store.require("JOB-0001").status is JobStatus.ESTIMATING


def test_valid_estimate_allows_receipted_readiness_transition(tmp_path: Path) -> None:
    coordinator, job_store, estimate_store = build_coordinator(tmp_path)
    seed_job(job_store)
    seed_estimate(estimate_store)

    result = coordinator.run(
        EstimateReadinessAgent(),
        readiness_context(),
        identity_verified=True,
    )

    assert result.status == "completed"
    assert result.output == {
        "job_id": "JOB-0001",
        "estimate_id": "EST-0001",
        "from_status": "estimating",
        "to_status": "ready-to-schedule",
    }
    assert job_store.require("JOB-0001").status is JobStatus.READY_TO_SCHEDULE
    assert result.receipt_id


def test_stale_job_status_blocks_transition(tmp_path: Path) -> None:
    coordinator, job_store, estimate_store = build_coordinator(tmp_path)
    seed_job(job_store)
    seed_estimate(estimate_store)
    job_store.transition("JOB-0001", JobStatus.READY_TO_SCHEDULE)

    with pytest.raises(ValueError, match="status changed"):
        coordinator.run(
            EstimateReadinessAgent(),
            readiness_context(),
            identity_verified=True,
        )
