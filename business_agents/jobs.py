"""Durable internal job records with explicit lifecycle transitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from business_agents.compatible_storage import CompatibleLockedJsonlFile


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
    """Locked append-only event store with legacy-read compatibility."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="job-event", version=1)

    def create(self, record: JobRecord) -> JobRecord:
        with self._storage.locked_file.locked():
            if self._get_unlocked(record.job_id) is not None:
                raise ValueError(f"job already exists: {record.job_id}")
            self._append_unlocked("created", record)
        return record

    def transition(self, job_id: str, target: JobStatus) -> JobRecord:
        with self._storage.locked_file.locked():
            current = self._get_unlocked(job_id)
            if current is None:
                raise KeyError(f"job not found: {job_id}")
            updated = current.transition(target)
            self._append_unlocked("transitioned", updated)
        return updated

    def get(self, job_id: str) -> JobRecord | None:
        with self._storage.locked_file.locked():
            return self._get_unlocked(job_id)

    def require(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        if record is None:
            raise KeyError(f"job not found: {job_id}")
        return record

    def list_current(self) -> tuple[JobRecord, ...]:
        with self._storage.locked_file.locked():
            records: dict[str, JobRecord] = {}
            for event in self._storage._read_all_unlocked():
                record = self._record_from_event(event)
                records[record.job_id] = record
            return tuple(records[key] for key in sorted(records))

    def _get_unlocked(self, job_id: str) -> JobRecord | None:
        current: JobRecord | None = None
        for event in self._storage._read_all_unlocked():
            if event.get("job_id") == job_id:
                current = self._record_from_event(event)
        return current

    def _append_unlocked(self, event_type: str, record: JobRecord) -> None:
        payload = asdict(record)
        payload["status"] = record.status.value
        payload["metadata"] = dict(record.metadata or {})
        payload["event_type"] = event_type
        envelope = {
            "_schema": self._storage.schema,
            "_version": self._storage.version,
            "data": payload,
        }
        import json, os
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

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
