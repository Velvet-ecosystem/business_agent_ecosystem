"""Read-only derived report snapshots."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class ReportSnapshot:
    report_id: str
    report_type: str
    scope_reference: str
    source_reference: str
    generated_by: str
    generated_at_reference: str

    def __post_init__(self) -> None:
        for name in (
            "report_id",
            "report_type",
            "scope_reference",
            "source_reference",
            "generated_by",
            "generated_at_reference",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class ReportSnapshotStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="report-snapshot")

    def create(self, snapshot: ReportSnapshot) -> ReportSnapshot:
        self._storage.append_unique(asdict(snapshot), field="report_id")
        return snapshot

    def get(self, report_id: str) -> ReportSnapshot | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("report_id") == report_id:
                return ReportSnapshot(**payload)
        return None
