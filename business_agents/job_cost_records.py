"""Append-only references for job-related costs and materials."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class JobCostRecord:
    record_id: str
    job_id: str
    category: str
    description: str
    amount_reference: str
    evidence_reference: str
    recorded_by: str

    def __post_init__(self) -> None:
        for name in ("record_id", "job_id", "category", "description", "amount_reference", "evidence_reference", "recorded_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class JobCostRecordStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="job-cost-record")

    def create(self, record: JobCostRecord) -> JobCostRecord:
        self._storage.append_unique(asdict(record), field="record_id")
        return record

    def get(self, record_id: str) -> JobCostRecord | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("record_id") == record_id:
                return JobCostRecord(**payload)
        return None
