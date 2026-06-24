from pathlib import Path

from business_agents.application import build_application
from business_agents.contracts import BusinessIntent
from business_agents.reconcile import attach


def test_attach_replaces_provider_executors(tmp_path: Path) -> None:
    application = build_application(tmp_path / "data")
    journal = attach(application, tmp_path / "operations.jsonl")

    booking = application.coordinator.executor_registry.resolve(
        BusinessIntent(route="calendar-booking", action="create-calendar-booking", subject_id="JOB-1")
    )
    delivery = application.coordinator.executor_registry.resolve(
        BusinessIntent(route="notification-delivery", action="deliver-notification-draft", subject_id="JOB-1")
    )

    assert booking.operation_journal is journal
    assert delivery.operation_journal is journal
