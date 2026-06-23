"""Fail-closed authority boundary with intent-bound, expiring grants."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from business_agents.contracts import AgentProposal, BusinessIntent


def intent_fingerprint(intent: BusinessIntent) -> str:
    """Return a deterministic SHA-256 fingerprint for an exact intent."""
    canonical = json.dumps(
        {
            "route": intent.route,
            "action": intent.action,
            "subject_id": intent.subject_id,
            "parameters": dict(intent.parameters),
            "risk_level": intent.risk_level.value,
            "approval_mode": intent.approval_mode.value,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class AuthorizationDecision:
    approved: bool
    authorization_id: str | None
    intent_fingerprint: str | None
    issued_at: float | None
    expires_at: float | None
    reason: str


@dataclass(frozen=True)
class AuthorizationGrant:
    intent_fingerprint: str
    issued_at: float
    expires_at: float


class CourtPolicy:
    """Issues one-use grants bound to an exact intent and short lifetime."""

    def __init__(
        self,
        *,
        grant_ttl_seconds: float = 30.0,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if grant_ttl_seconds <= 0:
            raise ValueError("grant_ttl_seconds must be positive")
        self.grant_ttl_seconds = float(grant_ttl_seconds)
        self._clock = clock
        self._active_grants: dict[str, AuthorizationGrant] = {}

    def evaluate(
        self,
        proposal: AgentProposal,
        *,
        identity_verified: bool,
        safety_passed: bool,
    ) -> AuthorizationDecision:
        self.cleanup_expired()
        if not identity_verified:
            return AuthorizationDecision(
                False,
                None,
                None,
                None,
                None,
                "identity-not-verified",
            )
        if not safety_passed:
            return AuthorizationDecision(
                False,
                None,
                None,
                None,
                None,
                "safety-check-failed",
            )

        issued_at = self._clock()
        expires_at = issued_at + self.grant_ttl_seconds
        fingerprint = intent_fingerprint(proposal.intent)
        authorization_id = f"auth_{uuid4().hex}"
        self._active_grants[authorization_id] = AuthorizationGrant(
            intent_fingerprint=fingerprint,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        return AuthorizationDecision(
            True,
            authorization_id,
            fingerprint,
            issued_at,
            expires_at,
            "approved",
        )

    def consume_authorization(
        self,
        authorization_id: str,
        intent: BusinessIntent,
    ) -> bool:
        """Consume a grant once, rejecting expiry, replay, or intent mutation."""
        grant = self._active_grants.pop(authorization_id, None)
        if grant is None:
            return False
        if self._clock() >= grant.expires_at:
            return False
        return hmac.compare_digest(
            grant.intent_fingerprint,
            intent_fingerprint(intent),
        )

    def cleanup_expired(self) -> int:
        """Remove expired grants and return the number purged."""
        now = self._clock()
        expired = [
            authorization_id
            for authorization_id, grant in self._active_grants.items()
            if now >= grant.expires_at
        ]
        for authorization_id in expired:
            del self._active_grants[authorization_id]
        return len(expired)

    @property
    def active_grant_count(self) -> int:
        self.cleanup_expired()
        return len(self._active_grants)
