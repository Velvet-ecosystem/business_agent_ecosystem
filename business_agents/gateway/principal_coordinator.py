"""Principal-aware wrapper around the existing business coordinator."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import ExecutorResult
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.identity import VerifiedPrincipal, legacy_verified_principal


class PrincipalBusinessCoordinator:
    """Requires a verified principal while preserving a temporary legacy bridge."""

    def __init__(self, coordinator: BusinessCoordinator) -> None:
        self.coordinator = coordinator

    def run(
        self,
        agent: BaseAgent,
        context: Mapping[str, Any],
        *,
        principal: VerifiedPrincipal | None = None,
        identity_verified: bool | None = None,
    ) -> ExecutorResult:
        if principal is not None and identity_verified is not None:
            raise ValueError("provide principal or identity_verified, not both")
        if principal is None and identity_verified is True:
            principal = legacy_verified_principal()
        if principal is None:
            raise PermissionError("identity-not-verified")

        enriched = dict(context)
        enriched["_principal_id"] = principal.principal_id
        enriched["_principal_display_name"] = principal.display_name
        enriched["_principal_role"] = principal.role
        enriched["_principal_session_id"] = principal.session_id
        enriched["_principal_presence_level"] = principal.presence_level.value

        return self.coordinator.run(
            agent,
            enriched,
            identity_verified=True,
        )
