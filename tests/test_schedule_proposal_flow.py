"""Integration tests for proposal-only scheduling."""

from pathlib import Path

import pytest

from business_agents.agents.scheduling_agent import SchedulingAgent
from business_agents.executors.registry import ExecutorRegistry
from business_agents.executors.schedule_proposal_executor import ScheduleProposalExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.schedule_proposal_safety_gate import ScheduleProposalSafetyGate
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.schedules import JsonlScheduleStore


def context() -> dict[str, object]:
    return {
        "proposal_id": "SCH-0001",
        "job_id": "JOB-0001",
        "job_status": "ready-to-schedule",
        "timezone": "America/Edmonton",
        "windows": [
            {"start": "2026-07-02T09:00:00-06:00", "end": "2026-07-02T12:00:00-06:00"},
            {"start": "2026-07-03T13:00:00-06:00", "end": "2026-07-03T17:00:00-06:00"},
        ],
    }


def build(tmp_path: Path):
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    schedules = JsonlScheduleStore(tmp_path / "schedules.jsonl")
    executor = ScheduleProposalExecutor(jobs, schedules, receipts)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=ScheduleProposalSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipts,
    )
    return coordinator, jobs, schedules


def seed(jobs: JsonlJobStore, status: JobStatus) -> None:
    jobs.create(JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
        status=status,
    ))


def test_valid_flow_stores_proposal_without_booking(tmp_path: Path) -> None:
    coordinator, jobs, schedules = build(tmp_path)
    seed(jobs, JobStatus.READY_TO_SCHEDULE)
    result = coordinator.run(SchedulingAgent(), context(), identity_verified=True)
    assert result.output["proposal_only"] is True
    assert result.output["window_count"] == 2
    assert schedules.get("SCH-0001") is not None
    assert jobs.require("JOB-0001").status is JobStatus.READY_TO_SCHEDULE
    assert result.receipt_id


def test_stale_job_state_blocks_proposal(tmp_path: Path) -> None:
    coordinator, jobs, _ = build(tmp_path)
    seed(jobs, JobStatus.SCHEDULED)
    with pytest.raises(ValueError, match="status changed"):
        coordinator.run(SchedulingAgent(), context(), identity_verified=True)


def test_duplicate_proposal_id_is_rejected(tmp_path: Path) -> None:
    coordinator, jobs, schedules = build(tmp_path)
    seed(jobs, JobStatus.READY_TO_SCHEDULE)
    coordinator.run(SchedulingAgent(), context(), identity_verified=True)
    with pytest.raises(ValueError, match="already exists"):
        coordinator.run(SchedulingAgent(), context(), identity_verified=True)
    assert schedules.get("SCH-0001") is not None
