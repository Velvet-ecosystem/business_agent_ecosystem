"""Durable completion evidence recorded before terminal job completion."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class CompletionEvidence:
    evidence_id: str
    job_id: str
    completed_by: str
    summary: str
    checklist: tuple[str, ...]
    artifact_refs: tuple[str, ...] = ()
    customer_acknowledged: bool = False
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("evidence_id", self.evidence_id),
            ("job_id", self.job_id),
            ("completed_by", self.completed_by),
            ("summary", self.summary),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.summary) > 4000:
            raise ValueError("summary is too long")
        if not self.checklist:
            raise ValueError("checklist must contain at least one item")
        if any(not isinstance(item, str) or not item.strip() for item in self.checklist):
            raise ValueError("checklist items must be non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in self.artifact_refs):
            raise ValueError("artifact references must be non-empty strings")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")


class CompletionEvidenceStore:
    """Locked append-only store allowing one evidence record per job."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="completion-evidence")

    def create(self, record: CompletionEvidence) -> CompletionEvidence:
        payload = asdict(record)
        payload["checklist"] = list(record.checklist)
        payload["artifact_refs"] = list(record.artifact_refs)
        payload["metadata"] = dict(record.metadata or {})
        with self._storage.locked_file.locked():
            items = self._storage._read_all_unlocked()
            if any(item.get("evidence_id") == record.evidence_id for item in items):
                raise ValueError(f"completion evidence already exists: {record.evidence_id}")
            if any(item.get("job_id") == record.job_id for item in items):
                raise ValueError(f"completion evidence already exists for job: {record.job_id}")
            self._append_unlocked(payload)
        return record

    def get(self, evidence_id: str) -> CompletionEvidence | None:
        return self._find("evidence_id", evidence_id)

    def get_by_job(self, job_id: str) -> CompletionEvidence | None:
        return self._find("job_id", job_id)

    def _find(self, field: str, value: str) -> CompletionEvidence | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get(field) == value:
                return CompletionEvidence(
                    evidence_id=str(payload["evidence_id"]),
                    job_id=str(payload["job_id"]),
                    completed_by=str(payload["completed_by"]),
                    summary=str(payload["summary"]),
                    checklist=tuple(str(item) for item in payload["checklist"]),
                    artifact_refs=tuple(str(item) for item in payload.get("artifact_refs", [])),
                    customer_acknowledged=bool(payload.get("customer_acknowledged", False)),
                    metadata=dict(payload.get("metadata", {})),
                )
        return None

    def _append_unlocked(self, payload: dict[str, object]) -> None:
        import json
        import os

        envelope = {"_schema": "completion-evidence", "_version": 1, "data": payload}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
