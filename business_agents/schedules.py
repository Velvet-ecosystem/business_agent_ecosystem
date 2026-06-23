"""Durable, proposal-only scheduling records."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


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
    """Append-only store for internal schedule proposals."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, proposal: ScheduleProposal) -> ScheduleProposal:
        if self.get(proposal.proposal_id) is not None:
            raise ValueError(f"schedule proposal already exists: {proposal.proposal_id}")
        payload = asdict(proposal)
        payload["windows"] = [
            {"start": window.start.isoformat(), "end": window.end.isoformat()}
            for window in proposal.windows
        ]
        payload["metadata"] = dict(proposal.metadata or {})
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        return proposal

    def get(self, proposal_id: str) -> ScheduleProposal | None:
        if not self.path.exists():
            return None
        found: ScheduleProposal | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid schedule proposal at line {line_number}") from exc
                if payload.get("proposal_id") == proposal_id:
                    found = ScheduleProposal(
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
        return found
