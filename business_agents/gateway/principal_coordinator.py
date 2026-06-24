"""Strict principal-aware wrapper around the business coordinator."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import ExecutorResult
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.identity import VerifiedPrincipal


class PrincipalBusinessCoordinator:
    """Requires an explicit verified principal for every public execution."""

    def __init__(self, coordinator: BusinessCoordinator) -> None:
        self.coordinator = coordinator

    def run(
        self,
        agent: BaseAgent,
        context: Mapping[str, Any],
        *,
        principal: VerifiedPrincipal,
    ) -> ExecutorResult:
        enriched = dict(context)
        enriched["_principal_id"] = principal.principal_id
        enriched["_principal_display_name"] = principal.display_name
        enriched["_principal_role"] = principal.role
        enriched["_principal_session_id"] = principal.session_id
        enriched["_principal_presence_level"] = principal.presence_level.value
        enriched["_principal_verified_at"] = principal.verified_at

        return self.coordinator.run(
            agent,
            enriched,
            identity_verified=True,
        )
