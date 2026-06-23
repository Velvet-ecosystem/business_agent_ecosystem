"""Calendar adapter boundary for externally persisted bookings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class CalendarEventRequest:
    idempotency_key: str
    title: str
    start: datetime
    end: datetime
    timezone: str
    description: str

    def __post_init__(self) -> None:
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        if not self.title.strip():
            raise ValueError("title is required")
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("calendar event times must be timezone-aware")
        if self.end <= self.start:
            raise ValueError("calendar event end must be after start")
        if not self.timezone.strip():
            raise ValueError("timezone is required")


@dataclass(frozen=True)
class CalendarEventResult:
    event_id: str
    idempotency_key: str
    created: bool

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.idempotency_key.strip():
            raise ValueError("event_id and idempotency_key are required")


class CalendarAdapter(Protocol):
    def create_event(self, request: CalendarEventRequest) -> CalendarEventResult:
        """Create or return the event bound to one idempotency key."""


class InMemoryCalendarAdapter:
    """Deterministic adapter for tests and local development."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.events: dict[str, CalendarEventResult] = {}
        self.requests: dict[str, CalendarEventRequest] = {}

    def create_event(self, request: CalendarEventRequest) -> CalendarEventResult:
        if self.fail:
            raise RuntimeError("calendar adapter failure")
        existing = self.events.get(request.idempotency_key)
        if existing is not None:
            return CalendarEventResult(
                event_id=existing.event_id,
                idempotency_key=existing.idempotency_key,
                created=False,
            )
        result = CalendarEventResult(
            event_id=f"evt_{len(self.events) + 1:04d}",
            idempotency_key=request.idempotency_key,
            created=True,
        )
        self.events[request.idempotency_key] = result
        self.requests[request.idempotency_key] = request
        return result
