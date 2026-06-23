"""Tests for the strongly approved calendar booking boundary."""

from datetime import datetime
from pathlib import Path

import pytest

from business_agents.agents.booking_agent import BookingAgent
from business_agents.booking_records import JsonlBookingStore
from business_agents.bookings import BookingPreparation, JsonlBookingPreparationStore
from business_agents.calendar_adapter import InMemoryCalendarAdapter
from business_agents.executors.booking_executor import BookingExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.booking_safety_gate import BookingSafetyGate
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def context(key: str = "book-JOB-0001-PREP-0001") -> dict[str, str]:
    return {
        "booking_id": "BOOK-0001",
        "job_id": "JOB-0001",
        "preparation_id": "PREP-0001",
        "idempotency_key": key,
        "job_status": "ready-to-schedule",
        "title": "Velvet installation",
        "description": "Approved workshop booking",
    }


def build(tmp_path: Path, *, fail: bool = False):
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    preparations = JsonlBookingPreparationStore(tmp_path / "preparations.jsonl")
    bookings = JsonlBookingStore(tmp_path / "bookings.jsonl")
    adapter = InMemoryCalendarAdapter(fail=fail)
    executor = BookingExecutor(jobs, preparations, bookings, adapter, receipts)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=BookingSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipts,
    )
    return coordinator, jobs, preparations, bookings, adapter


def seed(jobs: JsonlJobStore, preparations: JsonlBookingPreparationStore) -> None:
    jobs.create(JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
        status=JobStatus.READY_TO_SCHEDULE,
    ))
    preparations.create(BookingPreparation(
        preparation_id="PREP-0001",
        proposal_id="SCH-0001",
        job_id="JOB-0001",
        selected_index=0,
        start=datetime.fromisoformat("2026-07-02T09:00:00-06:00"),
        end=datetime.fromisoformat("2026-07-02T12:00:00-06:00"),
        timezone="America/Edmonton",
    ))


def test_successful_booking_creates_event_then_schedules_job(tmp_path: Path) -> None:
    coordinator, jobs, preparations, bookings, adapter = build(tmp_path)
    seed(jobs, preparations)
    result = coordinator.run(BookingAgent(), context(), identity_verified=True)
    assert result.output["calendar_event_created_now"] is True
    assert result.output["event_id"] == "evt_0001"
    assert jobs.require("JOB-0001").status is JobStatus.SCHEDULED
    assert bookings.get("BOOK-0001") is not None
    assert len(adapter.events) == 1


def test_retry_with_same_key_does_not_duplicate_event(tmp_path: Path) -> None:
    coordinator, jobs, preparations, _, adapter = build(tmp_path)
    seed(jobs, preparations)
    first = coordinator.run(BookingAgent(), context(), identity_verified=True)
    second = coordinator.run(BookingAgent(), context(), identity_verified=True)
    assert first.output["event_id"] == second.output["event_id"]
    assert second.output["calendar_event_created_now"] is False
    assert len(adapter.events) == 1


def test_adapter_failure_leaves_job_ready_to_schedule(tmp_path: Path) -> None:
    coordinator, jobs, preparations, bookings, adapter = build(tmp_path, fail=True)
    seed(jobs, preparations)
    with pytest.raises(RuntimeError, match="calendar adapter failure"):
        coordinator.run(BookingAgent(), context(), identity_verified=True)
    assert jobs.require("JOB-0001").status is JobStatus.READY_TO_SCHEDULE
    assert bookings.get("BOOK-0001") is None
    assert adapter.events == {}


def test_scheduled_job_cannot_create_second_booking(tmp_path: Path) -> None:
    coordinator, jobs, preparations, _, adapter = build(tmp_path)
    seed(jobs, preparations)
    coordinator.run(BookingAgent(), context(), identity_verified=True)
    with pytest.raises(ValueError, match="cannot create another booking"):
        coordinator.run(
            BookingAgent(),
            {**context("different-key"), "booking_id": "BOOK-0002"},
            identity_verified=True,
        )
    assert len(adapter.events) == 1
