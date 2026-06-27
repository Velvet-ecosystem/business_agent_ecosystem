"""Append-only change order records with explicit lineage."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class ChangeOrder:
    change_order_id: str
    job_id: str
    version: int
    reason: str
    scope_delta: str
    cost_impact_reference: str
    schedule_impact_reference: str
    proposed_by: str

    def __post_init__(self) -> None:
        for name in ("change_order_id", "job_id", "reason", "scope_delta", "cost_impact_reference", "schedule_impact_reference", "proposed_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.version, int) or self.version < 1:
            raise ValueError("version must be a positive integer")


class ChangeOrderStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="change-order")

    def create(self, record: ChangeOrder) -> ChangeOrder:
        latest = self.latest_for_job(record.job_id)
        expected = 1 if latest is None else latest.version + 1
        if record.version != expected:
            raise ValueError(f"change order version must be {expected}")
        self._storage.append_unique(asdict(record), field="change_order_id")
        return record

    def get(self, change_order_id: str) -> ChangeOrder | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("change_order_id") == change_order_id:
                return ChangeOrder(**payload)
        return None

    def latest_for_job(self, job_id: str) -> ChangeOrder | None:
        matches = [ChangeOrder(**payload) for payload in self._storage.read_all() if payload.get("job_id") == job_id]
        return max(matches, key=lambda item: item.version) if matches else None
