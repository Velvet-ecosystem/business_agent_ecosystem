"""Durable internal job records with explicit lifecycle transitions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class JobStatus(str, Enum):
    INTAKE_REVIEW = "intake-review"
    APPROVED = "approved"
    ESTIMATING = "estimating"
    READY_TO_SCHEDULE = "ready-to-schedule"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.INTAKE_REVIEW: frozenset({JobStatus.APPROVED, JobStatus.CANCELLED}),
    JobStatus.APPROVED: frozenset({JobStatus.ESTIMATING, JobStatus.CANCELLED}),
    JobStatus.ESTIMATING: frozenset({JobStatus.READY_TO_SCHEDULE, JobStatus.CANCELLED}),
    JobStatus.READY_TO_SCHEDULE: frozenset({JobStatus.SCHEDULED, JobStatus.CANCELLED}),
    JobStatus.SCHEDULED: frozenset({JobStatus.IN_PROGRESS, JobStatus.CANCELLED}),
    JobStatus.IN_PROGRESS: frozenset({JobStatus.COMPLETED, JobStatus.CANCELLED}),
    JobStatus.COMPLETED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    customer_name: str
    contact: str
    request: str
    source: str
    status: JobStatus = JobStatus.INTAKE_REVIEW
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("job_id", self.job_id),
            ("customer_name", self.customer_name),
            ("contact", self.contact),
            ("request", self.request),
            ("source", self.source),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.status, JobStatus):
            raise ValueError("status must be a JobStatus")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")

    def transition(self, target: JobStatus) -> "JobRecord":
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"invalid job transition: {self.status.value} -> {target.value}")
        return replace(self, status=target)


class JsonlJobStore:
    """Append-only JSONL event store that reconstructs current job state."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, record: JobRecord) -> JobRecord:
        if self.get(record.job_id) is not None:
            raise ValueError(f"job already exists: {record.job_id}")
        self._append("created", record)
        return record

    def transition(self, job_id: str, target: JobStatus) -> JobRecord:
        current = self.require(job_id)
        updated = current.transition(target)
        self._append("transitioned", updated)
        return updated

    def get(self, job_id: str) -> JobRecord | None:
        current: JobRecord | None = None
        for event in self._read_events():
            if event.get("job_id") == job_id:
                current = self._record_from_event(event)
        return current

    def require(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        if record is None:
            raise KeyError(f"job not found: {job_id}")
        return record

    def list_current(self) -> tuple[JobRecord, ...]:
        records: dict[str, JobRecord] = {}
        for event in self._read_events():
            record = self._record_from_event(event)
            records[record.job_id] = record
        return tuple(records[key] for key in sorted(records))

    def _append(self, event_type: str, record: JobRecord) -> None:
        payload = asdict(record)
        payload["status"] = record.status.value
        payload["metadata"] = dict(record.metadata or {})
        payload["event_type"] = event_type
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")

    def _read_events(self) -> tuple[dict[str, Any], ...]:
        if not self.path.exists():
            return ()
        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    event = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid job event at line {line_number}") from exc
                if not isinstance(event, dict):
                    raise ValueError(f"invalid job event at line {line_number}")
                events.append(event)
        return tuple(events)

    @staticmethod
    def _record_from_event(event: Mapping[str, Any]) -> JobRecord:
        return JobRecord(
            job_id=str(event["job_id"]),
            customer_name=str(event["customer_name"]),
            contact=str(event["contact"]),
            request=str(event["request"]),
            source=str(event["source"]),
            status=JobStatus(str(event["status"])),
            metadata=dict(event.get("metadata", {})),
        )
