"""Authoritative composition root for the Velvet business-agent application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from business_agents.booking_records import JsonlBookingStore
from business_agents.bookings import JsonlBookingPreparationStore
from business_agents.calendar_adapter import CalendarAdapter, InMemoryCalendarAdapter
from business_agents.delivery_adapter import DeliveryAdapter, InMemoryDeliveryAdapter
from business_agents.delivery_records import JsonlDeliveryStore
from business_agents.estimates import JsonlEstimateStore
from business_agents.executors.booking_executor import BookingExecutor
from business_agents.executors.booking_preparation_executor import BookingPreparationExecutor
from business_agents.executors.estimate_executor import EstimateExecutor
from business_agents.executors.estimate_readiness_executor import EstimateReadinessExecutor
from business_agents.executors.job_executor import JobExecutor
from business_agents.executors.job_transition_executor import JobTransitionExecutor
from business_agents.executors.notification_delivery_executor import NotificationDeliveryExecutor
from business_agents.executors.notification_draft_executor import NotificationDraftExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.executors.schedule_proposal_executor import ScheduleProposalExecutor
from business_agents.executors.work_start_executor import WorkStartExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.booking_preparation_safety_gate import BookingPreparationSafetyGate
from business_agents.gateway.booking_safety_gate import BookingSafetyGate
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.estimate_readiness_safety_gate import EstimateReadinessSafetyGate
from business_agents.gateway.estimate_safety_gate import EstimateDraftSafetyGate
from business_agents.gateway.job_safety_gate import JobRecordSafetyGate
from business_agents.gateway.job_transition_safety_gate import JobTransitionSafetyGate
from business_agents.gateway.notification_delivery_safety_gate import NotificationDeliverySafetyGate
from business_agents.gateway.notification_draft_safety_gate import NotificationDraftSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_registry import SafetyGateRegistry
from business_agents.gateway.schedule_proposal_safety_gate import ScheduleProposalSafetyGate
from business_agents.gateway.work_start_safety_gate import WorkStartSafetyGate
from business_agents.jobs import JsonlJobStore
from business_agents.notifications import JsonlNotificationDraftStore
from business_agents.schedules import JsonlScheduleStore
from business_agents.work_start import JsonlWorkStartStore


@dataclass(frozen=True)
class ApplicationStores:
    receipts: JsonlReceiptStore
    jobs: JsonlJobStore
    estimates: JsonlEstimateStore
    schedules: JsonlScheduleStore
    preparations: JsonlBookingPreparationStore
    bookings: JsonlBookingStore
    notification_drafts: JsonlNotificationDraftStore
    deliveries: JsonlDeliveryStore
    work_starts: JsonlWorkStartStore


@dataclass(frozen=True)
class BusinessApplication:
    coordinator: BusinessCoordinator
    stores: ApplicationStores
    safety_routes: tuple[str, ...]
    executor_routes: tuple[str, ...]
    calendar_adapter: CalendarAdapter
    delivery_adapter: DeliveryAdapter


def build_application(
    data_dir: Path,
    *,
    calendar_adapter: CalendarAdapter | None = None,
    delivery_adapter: DeliveryAdapter | None = None,
    court: CourtPolicy | None = None,
) -> BusinessApplication:
    """Build one coherent application graph from a single data directory."""

    data_dir.mkdir(parents=True, exist_ok=True)
    stores = ApplicationStores(
        receipts=JsonlReceiptStore(data_dir / "receipts.jsonl"),
        jobs=JsonlJobStore(data_dir / "jobs.jsonl"),
        estimates=JsonlEstimateStore(data_dir / "estimates.jsonl"),
        schedules=JsonlScheduleStore(data_dir / "schedules.jsonl"),
        preparations=JsonlBookingPreparationStore(data_dir / "booking_preparations.jsonl"),
        bookings=JsonlBookingStore(data_dir / "bookings.jsonl"),
        notification_drafts=JsonlNotificationDraftStore(data_dir / "notification_drafts.jsonl"),
        deliveries=JsonlDeliveryStore(data_dir / "deliveries.jsonl"),
        work_starts=JsonlWorkStartStore(data_dir / "work_starts.jsonl"),
    )

    calendar = calendar_adapter or InMemoryCalendarAdapter()
    delivery = delivery_adapter or InMemoryDeliveryAdapter()

    safety_registry = SafetyGateRegistry(
        [
            JobRecordSafetyGate(),
            JobTransitionSafetyGate(),
            EstimateDraftSafetyGate(),
            EstimateReadinessSafetyGate(),
            ScheduleProposalSafetyGate(),
            BookingPreparationSafetyGate(),
            BookingSafetyGate(),
            NotificationDraftSafetyGate(),
            NotificationDeliverySafetyGate(),
            WorkStartSafetyGate(),
        ]
    )

    executor_registry = ExecutorRegistry(
        [
            JobExecutor(stores.jobs, stores.receipts),
            JobTransitionExecutor(stores.jobs, stores.receipts),
            EstimateExecutor(stores.estimates, stores.receipts),
            EstimateReadinessExecutor(stores.jobs, stores.estimates, stores.receipts),
            ScheduleProposalExecutor(stores.jobs, stores.schedules, stores.receipts),
            BookingPreparationExecutor(
                stores.jobs,
                stores.schedules,
                stores.preparations,
                stores.receipts,
            ),
            BookingExecutor(
                stores.jobs,
                stores.preparations,
                stores.bookings,
                calendar,
                stores.receipts,
            ),
            NotificationDraftExecutor(
                stores.jobs,
                stores.bookings,
                stores.notification_drafts,
                stores.receipts,
            ),
            NotificationDeliveryExecutor(
                stores.jobs,
                stores.notification_drafts,
                stores.deliveries,
                delivery,
                stores.receipts,
            ),
            WorkStartExecutor(
                stores.jobs,
                stores.bookings,
                stores.work_starts,
                stores.receipts,
            ),
        ]
    )

    if safety_registry.routes != executor_registry.routes:
        missing_gates = sorted(set(executor_registry.routes) - set(safety_registry.routes))
        missing_executors = sorted(set(safety_registry.routes) - set(executor_registry.routes))
        raise RuntimeError(
            "application route mismatch: "
            f"missing_gates={missing_gates}, missing_executors={missing_executors}"
        )

    coordinator = BusinessCoordinator(
        court=court or CourtPolicy(),
        safety_gate=safety_registry,
        executor_registry=executor_registry,
        receipt_store=stores.receipts,
    )
    return BusinessApplication(
        coordinator=coordinator,
        stores=stores,
        safety_routes=safety_registry.routes,
        executor_routes=executor_registry.routes,
        calendar_adapter=calendar,
        delivery_adapter=delivery,
    )
