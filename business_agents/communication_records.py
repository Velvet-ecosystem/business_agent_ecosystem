"""Append-only communication history records."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class CommunicationRecord:
    record_id: str
    job_id: str
    customer_reference: str
    channel: str
    direction: str
    subject_reference: str
    content_reference: str
    recorded_by: str

    def __post_init__(self) -> None:
        for name in (
            "record_id",
            "job_id",
            "customer_reference",
            "channel",
            "direction",
            "subject_reference",
            "content_reference",
            "recorded_by",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.direction not in {"inbound", "outbound"}:
            raise ValueError("direction must be inbound or outbound")


class CommunicationRecordStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="communication-record")

    def create(self, record: CommunicationRecord) -> CommunicationRecord:
        self._storage.append_unique(asdict(record), field="record_id")
        return record

    def get(self, record_id: str) -> CommunicationRecord | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("record_id") == record_id:
                return CommunicationRecord(**payload)
        return None

    def list_for_job(self, job_id: str) -> tuple[CommunicationRecord, ...]:
        return tuple(
            CommunicationRecord(**payload)
            for payload in self._storage.read_all()
            if payload.get("job_id") == job_id
        )

    def list_for_customer(self, customer_reference: str) -> tuple[CommunicationRecord, ...]:
        if not isinstance(customer_reference, str) or not customer_reference.strip():
            raise ValueError("customer_reference must be a non-empty string")
        return tuple(
            CommunicationRecord(**payload)
            for payload in self._storage.read_all()
            if payload.get("customer_reference") == customer_reference
        )
