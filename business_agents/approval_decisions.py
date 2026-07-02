"""Append-only human decisions that do not grant execution authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


class ApprovalDecisionValue(str, Enum):
    APPROVE = "approve"
    DENY = "deny"


@dataclass(frozen=True)
class ApprovalDecision:
    decision_id: str
    request_id: str
    decision: ApprovalDecisionValue
    decided_by: str
    rationale: str
    strong_confirmation: bool

    def __post_init__(self) -> None:
        for name in ("decision_id", "request_id", "decided_by", "rationale"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.decision, ApprovalDecisionValue):
            raise ValueError("decision must be an ApprovalDecisionValue")
        if not isinstance(self.strong_confirmation, bool):
            raise ValueError("strong_confirmation must be a bool")


class ApprovalDecisionStore:
    """One append-only human decision per approval request."""

    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="approval-decision", version=1)

    def create(self, decision: ApprovalDecision) -> ApprovalDecision:
        if self.get_for_request(decision.request_id) is not None:
            raise ValueError(f"decision already exists for request: {decision.request_id}")
        payload = asdict(decision)
        payload["decision"] = decision.decision.value
        self._storage.append_unique(payload, field="decision_id")
        return decision

    def get_for_request(self, request_id: str) -> ApprovalDecision | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("request_id") == request_id:
                return ApprovalDecision(
                    decision_id=str(payload["decision_id"]),
                    request_id=str(payload["request_id"]),
                    decision=ApprovalDecisionValue(str(payload["decision"])),
                    decided_by=str(payload["decided_by"]),
                    rationale=str(payload["rationale"]),
                    strong_confirmation=bool(payload["strong_confirmation"]),
                )
        return None
