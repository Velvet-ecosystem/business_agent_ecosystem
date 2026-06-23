"""Integration tests for work-start execution."""

from datetime import datetime
from pathlib import Path

import pytest

from business_agents.agents.work_start_agent import WorkStartAgent
from business_agents.booking_records import BookingRecord, JsonlBookingStore
from business_agents.executors.registry import ExecutorRegistry
from business_agents.executors.work_start_executor import WorkStartExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.work_start_safety_gate import WorkStartSafetyGate
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.work_start import JsonlWorkStartStore


def context() -> dict[str, str]:
    return {
        "start_id": "START-0001",
        "job_id": "JOB-0001",
        "booking_id": "BOOK-0001",
        "started_by": "Mister",
        "reason": "Vehicle and work bay are ready.",
        "job_status": "scheduled",
    }


def build(tmp_path: Path):
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    bookings = JsonlBookingStore(tmp_path / "bookings.jsonl")
    starts = JsonlWorkStartStore(tmp_path / "starts.jsonl")
    executor = WorkStartExecutor(jobs, bookings, starts, receipts)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=WorkStartSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipts,
    )
    return coordinator, jobs, bookings, starts


def seed(jobs: JsonlJobStore, bookings: JsonlBookingStore, booking_job: str = "JOB-0001") -> None:
    jobs.create(JobRecord("JOB-0001", "Alex", "alex@example.com", "Install Velvet", "manual", JobStatus.SCHEDULED))
    bookings.create(BookingRecord(
        booking_id="BOOK-0001",
        job_id=booking_job,
        preparation_id="PREP-0001",
        idempotency_key="book-JOB-0001-PREP-0001",
        event_id="evt_0001",
        start=datetime.fromisoformat("2026-07-02T09:00:00-06:00"),
        end=datetime.fromisoformat("2026-07-02T12:00:00-06:00"),
        timezone="America/Edmonton",
    ))


def test_valid_start_moves_job_to_in_progress(tmp_path: Path) -> None:
    coordinator, jobs, bookings, starts = build(tmp_path)
    seed(jobs, bookings)
    result = coordinator.run(WorkStartAgent(), context(), identity_verified=True)
    assert result.output["to_status"] == "in-progress"
    assert jobs.require("JOB-0001").status is JobStatus.IN_PROGRESS
    assert starts.get("START-0001") is not None


def test_missing_or_wrong_booking_blocks_start(tmp_path: Path) -> None:
    coordinator, jobs, bookings, _ = build(tmp_path)
    jobs.create(JobRecord("JOB-0001", "Alex", "a@example.com", "Install", "manual", JobStatus.SCHEDULED))
    with pytest.raises(ValueError, match="booking record not found"):
        coordinator.run(WorkStartAgent(), context(), identity_verified=True)

    bookings.create(BookingRecord(
        booking_id="BOOK-0001",
        job_id="JOB-9999",
        preparation_id="PREP-X",
        idempotency_key="other",
        event_id="evt_x",
        start=datetime.fromisoformat("2026-07-02T09:00:00-06:00"),
        end=datetime.fromisoformat("2026-07-02T12:00:00-06:00"),
        timezone="America/Edmonton",
    ))
    with pytest.raises(ValueError, match="different job"):
        coordinator.run(WorkStartAgent(), context(), identity_verified=True)
