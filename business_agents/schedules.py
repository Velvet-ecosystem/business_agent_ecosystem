"""Durable, proposal-only scheduling records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class ScheduleWindow:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("schedule windows must be timezone-aware")
        if self.end <= self.start:
            raise ValueError("schedule window end must be after start")


@dataclass(frozen=True)
class ScheduleProposal:
    proposal_id: str
    job_id: str
    timezone: str
    windows: tuple[ScheduleWindow, ...]
    notes: str = ""
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name, value in (("proposal_id", self.proposal_id), ("job_id", self.job_id), ("timezone", self.timezone)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not 1 <= len(self.windows) <= 10:
            raise ValueError("schedule proposal must contain between 1 and 10 windows")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")


class JsonlScheduleStore:
    """Locked append-only schedule proposal store with legacy compatibility."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="schedule-proposal")

    def create(self, proposal: ScheduleProposal) -> ScheduleProposal:
        payload = asdict(proposal)
        payload["windows"] = [
            {"start": window.start.isoformat(), "end": window.end.isoformat()}
            for window in proposal.windows
        ]
        payload["metadata"] = dict(proposal.metadata or {})
        self._storage.append_unique(payload, field="proposal_id")
        return proposal

    def get(self, proposal_id: str) -> ScheduleProposal | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("proposal_id") == proposal_id:
                return ScheduleProposal(
                    proposal_id=str(payload["proposal_id"]),
                    job_id=str(payload["job_id"]),
                    timezone=str(payload["timezone"]),
                    windows=tuple(
                        ScheduleWindow(
                            start=datetime.fromisoformat(str(item["start"])),
                            end=datetime.fromisoformat(str(item["end"])),
                        )
                        for item in payload["windows"]
                    ),
                    notes=str(payload.get("notes", "")),
                    metadata=dict(payload.get("metadata", {})),
                )
        return None
