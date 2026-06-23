"""Tests for exact-window booking preparation."""

from datetime import datetime
from pathlib import Path

import pytest

from business_agents.agents.booking_preparation_agent import BookingPreparationAgent
from business_agents.bookings import JsonlBookingPreparationStore
from business_agents.executors.booking_preparation_executor import BookingPreparationExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.booking_preparation_safety_gate import BookingPreparationSafetyGate
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.schedules import JsonlScheduleStore, ScheduleProposal, ScheduleWindow


def context(index: int = 1) -> dict[str, object]:
    return {
        "preparation_id": "PREP-0001",
        "proposal_id": "SCH-0001",
        "job_id": "JOB-0001",
        "job_status": "ready-to-schedule",
        "selected_index": index,
        "notes": "Internal preparation only",
    }


def build(tmp_path: Path):
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    schedules = JsonlScheduleStore(tmp_path / "schedules.jsonl")
    preparations = JsonlBookingPreparationStore(tmp_path / "preparations.jsonl")
    executor = BookingPreparationExecutor(jobs, schedules, preparations, receipts)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=BookingPreparationSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipts,
    )
    return coordinator, jobs, schedules, preparations


def seed(jobs: JsonlJobStore, schedules: JsonlScheduleStore, proposal_job: str = "JOB-0001") -> None:
    jobs.create(JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
        status=JobStatus.READY_TO_SCHEDULE,
    ))
    schedules.create(ScheduleProposal(
        proposal_id="SCH-0001",
        job_id=proposal_job,
        timezone="America/Edmonton",
        windows=(
            ScheduleWindow(datetime.fromisoformat("2026-07-02T09:00:00-06:00"), datetime.fromisoformat("2026-07-02T12:00:00-06:00")),
            ScheduleWindow(datetime.fromisoformat("2026-07-03T13:00:00-06:00"), datetime.fromisoformat("2026-07-03T17:00:00-06:00")),
        ),
    ))


def test_selected_window_is_bound_to_stored_proposal(tmp_path: Path) -> None:
    coordinator, jobs, schedules, preparations = build(tmp_path)
    seed(jobs, schedules)
    result = coordinator.run(BookingPreparationAgent(), context(), identity_verified=True)
    assert result.output["selected_index"] == 1
    assert result.output["start"] == "2026-07-03T13:00:00-06:00"
    assert result.output["booking_created"] is False
    stored = preparations.get("PREP-0001")
    assert stored is not None
    assert stored.proposal_id == "SCH-0001"
    assert jobs.require("JOB-0001").status is JobStatus.READY_TO_SCHEDULE


def test_missing_schedule_proposal_blocks_preparation(tmp_path: Path) -> None:
    coordinator, jobs, _, _ = build(tmp_path)
    jobs.create(JobRecord("JOB-0001", "Alex", "a@example.com", "Install", "manual", JobStatus.READY_TO_SCHEDULE))
    with pytest.raises(ValueError, match="schedule proposal not found"):
        coordinator.run(BookingPreparationAgent(), context(), identity_verified=True)


def test_wrong_job_proposal_blocks_preparation(tmp_path: Path) -> None:
    coordinator, jobs, schedules, _ = build(tmp_path)
    seed(jobs, schedules, proposal_job="JOB-9999")
    with pytest.raises(ValueError, match="different job"):
        coordinator.run(BookingPreparationAgent(), context(), identity_verified=True)


def test_out_of_range_index_blocks_preparation(tmp_path: Path) -> None:
    coordinator, jobs, schedules, _ = build(tmp_path)
    seed(jobs, schedules)
    with pytest.raises(ValueError, match="does not exist"):
        coordinator.run(BookingPreparationAgent(), context(index=8), identity_verified=True)


def test_extra_fields_are_rejected() -> None:
    proposal = BookingPreparationAgent().propose(context())
    intent_type = type(proposal.intent)
    altered = intent_type(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "calendar_event_id": "evt-1"},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )
    decision = BookingPreparationSafetyGate().evaluate(altered)
    assert decision.passed is False
    assert decision.reason == "unexpected-booking-preparation-fields"
