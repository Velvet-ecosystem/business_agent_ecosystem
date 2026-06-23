"""Tests for authoritative application assembly."""

from pathlib import Path

from business_agents.application import build_application
from business_agents.calendar_adapter import InMemoryCalendarAdapter
from business_agents.delivery_adapter import InMemoryDeliveryAdapter


def test_application_builds_matching_route_registries(tmp_path: Path) -> None:
    application = build_application(tmp_path)

    assert application.safety_routes == application.executor_routes
    assert application.safety_routes == (
        "booking-preparation",
        "calendar-booking",
        "estimate-draft",
        "estimate-readiness",
        "job-record",
        "job-transition",
        "notification-delivery",
        "notification-draft",
        "schedule-proposal",
        "work-start",
    )


def test_application_uses_one_data_directory(tmp_path: Path) -> None:
    application = build_application(tmp_path)

    paths = {
        application.stores.receipts.path,
        application.stores.jobs.path,
        application.stores.estimates.path,
        application.stores.schedules.path,
        application.stores.preparations.path,
        application.stores.bookings.path,
        application.stores.notification_drafts.path,
        application.stores.deliveries.path,
        application.stores.work_starts.path,
    }

    assert len(paths) == 9
    assert all(path.parent == tmp_path for path in paths)


def test_application_accepts_explicit_provider_adapters(tmp_path: Path) -> None:
    calendar = InMemoryCalendarAdapter()
    delivery = InMemoryDeliveryAdapter()

    application = build_application(
        tmp_path,
        calendar_adapter=calendar,
        delivery_adapter=delivery,
    )

    assert application.calendar_adapter is calendar
    assert application.delivery_adapter is delivery
