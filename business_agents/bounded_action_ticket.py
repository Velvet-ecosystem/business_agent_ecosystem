"""Inert single-use action ticket contract with exact scope and expiry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from business_agents.bound_artifact_scope import BoundArtifactScope


class BoundedActionTicketStatus(str, Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    REVOKED = "revoked"


@dataclass(frozen=True)
class BoundedActionTicket:
    ticket_id: str
    approval_request_id: str
    decision_id: str
    binding: BoundArtifactScope
    issued_by: str
    issued_at: datetime
    expires_at: datetime
    max_uses: int = 1
    uses: int = 0
    status: BoundedActionTicketStatus = BoundedActionTicketStatus.ACTIVE

    def __post_init__(self) -> None:
        for name in ("ticket_id", "approval_request_id", "decision_id", "issued_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.binding, BoundArtifactScope):
            raise ValueError("binding must be a BoundArtifactScope")
        if self.issued_by != "Court":
            raise ValueError("bounded action tickets must be issued by Court")
        for name in ("issued_at", "expires_at"):
            value = getattr(self, name)
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        if self.max_uses != 1:
            raise ValueError("bounded action tickets must be single-use")
        if self.uses not in {0, 1}:
            raise ValueError("uses must be zero or one")
        if not isinstance(self.status, BoundedActionTicketStatus):
            raise ValueError("status must be a BoundedActionTicketStatus")
        if self.status is BoundedActionTicketStatus.ACTIVE and self.uses != 0:
            raise ValueError("active ticket cannot already be used")
        if self.status is BoundedActionTicketStatus.CONSUMED and self.uses != 1:
            raise ValueError("consumed ticket must have exactly one use")

    def is_live(self, now: datetime) -> bool:
        if not isinstance(now, datetime) or now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        return (
            self.status is BoundedActionTicketStatus.ACTIVE
            and self.uses == 0
            and self.issued_at <= now < self.expires_at
        )

    def matches(
        self,
        *,
        artifact_id: str,
        artifact_digest: str,
        route: str,
        action: str,
        subject_id: str,
        handler_id: str,
    ) -> bool:
        return self.binding.matches(
            artifact_id=artifact_id,
            artifact_digest=artifact_digest,
            route=route,
            action=action,
            subject_id=subject_id,
            handler_id=handler_id,
        )
