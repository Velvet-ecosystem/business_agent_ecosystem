from pathlib import Path

from business_agents.executors.booking_executor import BookingExecutor
from business_agents.executors.notification_delivery_executor import NotificationDeliveryExecutor
from business_agents.external_operations import ExternalOperationJournal


def attach(application, path: Path) -> ExternalOperationJournal:
    journal = ExternalOperationJournal(path)
    stores = application.stores
    registry = application.coordinator.executor_registry
    registry.replace(BookingExecutor(
        stores.jobs, stores.preparations, stores.bookings,
        application.calendar_adapter, stores.receipts, journal,
    ))
    registry.replace(NotificationDeliveryExecutor(
        stores.jobs, stores.notification_drafts, stores.deliveries,
        application.delivery_adapter, stores.receipts, journal,
    ))
    return journal
