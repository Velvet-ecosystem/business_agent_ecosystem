"""Fail-closed authority boundary with intent-bound, one-use grants."""

from __future__ import annotations

import hashlib
import hmac
import json
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
    reason: str


class CourtPolicy:
    """Issues one-use grants bound to the exact approved intent."""

    def __init__(self) -> None:
        self._active_grants: dict[str, str] = {}

    def evaluate(
        self,
        proposal: AgentProposal,
        *,
        identity_verified: bool,
        safety_passed: bool,
    ) -> AuthorizationDecision:
        if not identity_verified:
            return AuthorizationDecision(
                False, None, None, "identity-not-verified"
            )
        if not safety_passed:
            return AuthorizationDecision(
                False, None, None, "safety-check-failed"
            )

        fingerprint = intent_fingerprint(proposal.intent)
        authorization_id = f"auth_{uuid4().hex}"
        self._active_grants[authorization_id] = fingerprint
        return AuthorizationDecision(
            True,
            authorization_id,
            fingerprint,
            "approved",
        )

    def consume_authorization(
        self,
        authorization_id: str,
        intent: BusinessIntent,
    ) -> bool:
        """Consume a grant once and verify it belongs to this exact intent."""
        expected = self._active_grants.pop(authorization_id, None)
        if expected is None:
            return False
        return hmac.compare_digest(expected, intent_fingerprint(intent))
