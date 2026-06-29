"""Durable records for work awaiting an explicit human decision."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.contracts import ApprovalMode, RiskLevel


class ApprovalRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    route: str
    action: str
    subject_id: str
    summary: str
    requested_by: str
    risk_level: RiskLevel
    approval_mode: ApprovalMode
    status: ApprovalRequestStatus = ApprovalRequestStatus.PENDING

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "route",
            "action",
            "subject_id",
            "summary",
            "requested_by",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.risk_level, RiskLevel):
            raise ValueError("risk_level must be a RiskLevel")
        if not isinstance(self.approval_mode, ApprovalMode):
            raise ValueError("approval_mode must be an ApprovalMode")
        if not isinstance(self.status, ApprovalRequestStatus):
            raise ValueError("status must be an ApprovalRequestStatus")
        if self.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} and self.approval_mode is ApprovalMode.POLICY:
            raise ValueError("high-risk approval requests cannot use policy-only approval")
        if self.risk_level is RiskLevel.CRITICAL and self.approval_mode is not ApprovalMode.STRONG_HUMAN:
            raise ValueError("critical approval requests require strong human approval")


class ApprovalRequestStore:
    """Append-only request store. Decision execution is intentionally absent."""

    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="approval-request", version=1)

    def create(self, request: ApprovalRequest) -> ApprovalRequest:
        payload = asdict(request)
        payload["risk_level"] = request.risk_level.value
        payload["approval_mode"] = request.approval_mode.value
        payload["status"] = request.status.value
        self._storage.append_unique(payload, field="request_id")
        return request

    def list_current(self) -> tuple[ApprovalRequest, ...]:
        return tuple(
            self._from_payload(payload)
            for payload in sorted(self._storage.read_all(), key=lambda item: str(item.get("request_id", "")))
        )

    def list_pending(self) -> tuple[ApprovalRequest, ...]:
        return tuple(request for request in self.list_current() if request.status is ApprovalRequestStatus.PENDING)

    @staticmethod
    def _from_payload(payload: dict) -> ApprovalRequest:
        return ApprovalRequest(
            request_id=str(payload["request_id"]),
            route=str(payload["route"]),
            action=str(payload["action"]),
            subject_id=str(payload["subject_id"]),
            summary=str(payload["summary"]),
            requested_by=str(payload["requested_by"]),
            risk_level=RiskLevel(str(payload["risk_level"])),
            approval_mode=ApprovalMode(str(payload["approval_mode"])),
            status=ApprovalRequestStatus(str(payload["status"])),
        )
