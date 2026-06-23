"""Tests for internal booking-confirmation drafts."""

from datetime import datetime
from pathlib import Path

import pytest

from business_agents.agents.notification_draft_agent import NotificationDraftAgent
from business_agents.booking_records import BookingRecord, JsonlBookingStore
from business_agents.executors.notification_draft_executor import NotificationDraftExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.notification_draft_safety_gate import NotificationDraftSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.notifications import JsonlNotificationDraftStore


def context() -> dict[str, str]:
    return {
        "draft_id": "NOTE-0001",
        "booking_id": "BOOK-0001",
        "job_id": "JOB-0001",
        "job_status": "scheduled",
        "template": "booking-confirmation",
    }


def build(tmp_path: Path):
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    bookings = JsonlBookingStore(tmp_path / "bookings.jsonl")
    drafts = JsonlNotificationDraftStore(tmp_path / "notifications.jsonl")
    executor = NotificationDraftExecutor(jobs, bookings, drafts, receipts)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=NotificationDraftSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipts,
    )
    return coordinator, jobs, bookings, drafts


def seed(jobs: JsonlJobStore, bookings: JsonlBookingStore, booking_job: str = "JOB-0001") -> None:
    jobs.create(JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
        status=JobStatus.SCHEDULED,
    ))
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


def test_valid_flow_builds_unsent_draft_from_durable_records(tmp_path: Path) -> None:
    coordinator, jobs, bookings, drafts = build(tmp_path)
    seed(jobs, bookings)
    result = coordinator.run(NotificationDraftAgent(), context(), identity_verified=True)
    assert result.output["sent"] is False
    assert result.output["recipient"] == "alex@example.com"
    draft = drafts.get("NOTE-0001")
    assert draft is not None
    assert "evt_0001" in draft.body
    assert "2026-07-02T09:00:00-06:00" in draft.body
    assert jobs.require("JOB-0001").status is JobStatus.SCHEDULED


def test_missing_booking_blocks_draft(tmp_path: Path) -> None:
    coordinator, jobs, _, _ = build(tmp_path)
    jobs.create(JobRecord("JOB-0001", "Alex", "a@example.com", "Install", "manual", JobStatus.SCHEDULED))
    with pytest.raises(ValueError, match="booking record not found"):
        coordinator.run(NotificationDraftAgent(), context(), identity_verified=True)


def test_booking_for_different_job_blocks_draft(tmp_path: Path) -> None:
    coordinator, jobs, bookings, _ = build(tmp_path)
    seed(jobs, bookings, booking_job="JOB-9999")
    with pytest.raises(ValueError, match="different job"):
        coordinator.run(NotificationDraftAgent(), context(), identity_verified=True)


def test_unscheduled_job_blocks_draft(tmp_path: Path) -> None:
    coordinator, jobs, bookings, _ = build(tmp_path)
    seed(jobs, bookings)
    jobs.transition("JOB-0001", JobStatus.IN_PROGRESS)
    with pytest.raises(ValueError, match="status changed"):
        coordinator.run(NotificationDraftAgent(), context(), identity_verified=True)


def test_safety_gate_rejects_caller_supplied_message_fields() -> None:
    proposal = NotificationDraftAgent().propose(context())
    intent_type = type(proposal.intent)
    altered = intent_type(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "body": "send this instead"},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )
    decision = NotificationDraftSafetyGate().evaluate(altered)
    assert decision.passed is False
    assert decision.reason == "unexpected-notification-fields"
