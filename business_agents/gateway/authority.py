"""Minimal fail-closed authority boundary for early framework tests."""

from __future__ import annotations

from dataclasses import dataclass

from business_agents.contracts import AgentProposal


@dataclass(frozen=True)
class AuthorizationDecision:
    approved: bool
    authorization_id: str | None
    reason: str


class CourtPolicy:
    """Evaluates proposals without exposing executor internals to agents."""

    def evaluate(self, proposal: AgentProposal, *, identity_verified: bool, safety_passed: bool) -> AuthorizationDecision:
        if not identity_verified:
            return AuthorizationDecision(False, None, "identity-not-verified")
        if not safety_passed:
            return AuthorizationDecision(False, None, "safety-check-failed")
        return AuthorizationDecision(True, f"auth:{proposal.agent_name}:{proposal.intent.route}", "approved")
