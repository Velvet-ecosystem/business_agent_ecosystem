"""Tests for strongly approved notification delivery."""

from pathlib import Path

import pytest

from business_agents.agents.notification_delivery_agent import NotificationDeliveryAgent
from business_agents.delivery_adapter import InMemoryDeliveryAdapter
from business_agents.delivery_records import JsonlDeliveryStore
from business_agents.executors.notification_delivery_executor import NotificationDeliveryExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.external_operations import ExternalOperationJournal, ExternalOperationState
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.notification_delivery_safety_gate import NotificationDeliverySafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.notifications import JsonlNotificationDraftStore, NotificationDraft


def context(key: str = "notify-JOB-0001-NOTE-0001") -> dict[str, str]:
    return {
        "delivery_id": "DEL-0001",
        "draft_id": "NOTE-0001",
        "job_id": "JOB-0001",
        "idempotency_key": key,
        "job_status": "scheduled",
    }


def build(tmp_path: Path, *, fail: bool = False):
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    drafts = JsonlNotificationDraftStore(tmp_path / "drafts.jsonl")
    deliveries = JsonlDeliveryStore(tmp_path / "deliveries.jsonl")
    operations = ExternalOperationJournal(tmp_path / "external_operations.jsonl")
    adapter = InMemoryDeliveryAdapter(fail=fail)
    executor = NotificationDeliveryExecutor(jobs, drafts, deliveries, adapter, receipts, operations)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=NotificationDeliverySafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipts,
    )
    return coordinator, jobs, drafts, deliveries, adapter, operations


def seed(jobs: JsonlJobStore, drafts: JsonlNotificationDraftStore) -> None:
    jobs.create(JobRecord(
        job_id="JOB-0001",
        customer_name="Alex Morgan",
        contact="alex@example.com",
        request="Install Velvet.",
        source="website-form",
        status=JobStatus.SCHEDULED,
    ))
    drafts.create(NotificationDraft(
        draft_id="NOTE-0001",
        job_id="JOB-0001",
        booking_id="BOOK-0001",
        channel="email",
        recipient="alex@example.com",
        subject="Booking confirmation",
        body="Your booking is confirmed.",
    ))


def test_delivery_sends_once_and_records_provider_id(tmp_path: Path) -> None:
    coordinator, jobs, drafts, deliveries, adapter, operations = build(tmp_path)
    seed(jobs, drafts)
    result = coordinator.run(NotificationDeliveryAgent(), context(), identity_verified=True)
    assert result.output["delivered_now"] is True
    assert result.output["provider_message_id"] == "msg_0001"
    assert deliveries.get("DEL-0001") is not None
    assert len(adapter.results) == 1
    assert operations.get("delivery:notify-JOB-0001-NOTE-0001").state is ExternalOperationState.LOCALLY_RECORDED


def test_retry_with_same_key_does_not_send_twice(tmp_path: Path) -> None:
    coordinator, jobs, drafts, _, adapter, _ = build(tmp_path)
    seed(jobs, drafts)
    first = coordinator.run(NotificationDeliveryAgent(), context(), identity_verified=True)
    second = coordinator.run(NotificationDeliveryAgent(), context(), identity_verified=True)
    assert first.output["provider_message_id"] == second.output["provider_message_id"]
    assert second.output["delivered_now"] is False
    assert len(adapter.results) == 1


def test_provider_failure_creates_no_delivery_record_and_journals_failure(tmp_path: Path) -> None:
    coordinator, jobs, drafts, deliveries, adapter, operations = build(tmp_path, fail=True)
    seed(jobs, drafts)
    with pytest.raises(RuntimeError, match="delivery adapter failure"):
        coordinator.run(NotificationDeliveryAgent(), context(), identity_verified=True)
    assert deliveries.get("DEL-0001") is None
    assert adapter.results == {}
    failed = operations.get("delivery:notify-JOB-0001-NOTE-0001")
    assert failed is not None
    assert failed.state is ExternalOperationState.FAILED
    assert "delivery adapter failure" in (failed.error or "")


def test_missing_draft_blocks_delivery(tmp_path: Path) -> None:
    coordinator, jobs, _, _, _, _ = build(tmp_path)
    jobs.create(JobRecord("JOB-0001", "Alex", "a@example.com", "Install", "manual", JobStatus.SCHEDULED))
    with pytest.raises(ValueError, match="notification draft not found"):
        coordinator.run(NotificationDeliveryAgent(), context(), identity_verified=True)
