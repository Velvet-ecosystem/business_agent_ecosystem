"""Agent that proposes bounded candidate scheduling windows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class SchedulingAgent(BaseAgent):
    """Prepares internal candidate windows without creating a booking."""

    def __init__(self) -> None:
        super().__init__("Scheduling Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        job_id = str(context.get("job_id", "")).strip()
        proposal_id = str(context.get("proposal_id", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        timezone = str(context.get("timezone", "")).strip()
        notes = str(context.get("notes", "")).strip()
        raw_windows = context.get("windows")

        if not job_id or not proposal_id or not timezone:
            raise ValueError("job_id, proposal_id, and timezone are required")
        if job_status != "ready-to-schedule":
            raise ValueError("job must be ready-to-schedule")
        if len(notes) > 2000:
            raise ValueError("notes are too long")
        try:
            zone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("unknown timezone") from exc
        if not isinstance(raw_windows, (list, tuple)) or not 1 <= len(raw_windows) <= 10:
            raise ValueError("windows must contain between 1 and 10 candidates")

        normalized: list[dict[str, str]] = []
        previous_end: datetime | None = None
        for item in raw_windows:
            if not isinstance(item, Mapping):
                raise ValueError("each window must be a mapping")
            try:
                start = datetime.fromisoformat(str(item["start"]))
                end = datetime.fromisoformat(str(item["end"]))
            except (KeyError, ValueError) as exc:
                raise ValueError("window timestamps must use ISO 8601") from exc
            if start.tzinfo is None or end.tzinfo is None:
                raise ValueError("window timestamps must include timezone offsets")
            start = start.astimezone(zone)
            end = end.astimezone(zone)
            if end <= start:
                raise ValueError("window end must be after start")
            if previous_end is not None and start < previous_end:
                raise ValueError("candidate windows must be ordered and non-overlapping")
            previous_end = end
            normalized.append({"start": start.isoformat(), "end": end.isoformat()})

        intent = BusinessIntent(
            route="schedule-proposal",
            action="create-schedule-proposal",
            subject_id=job_id,
            parameters={
                "proposal_id": proposal_id,
                "job_id": job_id,
                "job_status": job_status,
                "timezone": timezone,
                "windows": tuple((item["start"], item["end"]) for item in normalized),
                "notes": notes,
            },
            risk_level=RiskLevel.MEDIUM,
            approval_mode=ApprovalMode.HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale="Candidate work windows are ready for internal review; no booking will be created.",
            confidence=0.95,
        )
