"""Compatibility wrapper for principal-aware business execution."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import ExecutorResult
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.verified_coordinator import bind_verified_principal
from business_agents.identity import VerifiedPrincipal


class PrincipalBusinessCoordinator:
    """Compatibility entry point with mandatory principal freshness checks.

    New integrations should prefer ``VerifiedBusinessCoordinator``. This name is
    retained so existing callers keep working while sharing the same binding law.
    """

    def __init__(self, coordinator: BusinessCoordinator, *, max_age_seconds: float = 300.0) -> None:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        self.coordinator = coordinator
        self.max_age_seconds = float(max_age_seconds)

    def run(
        self,
        agent: BaseAgent,
        context: Mapping[str, Any],
        *,
        principal: VerifiedPrincipal,
    ) -> ExecutorResult:
        enriched = bind_verified_principal(
            context,
            principal,
            max_age_seconds=self.max_age_seconds,
        )
        return self.coordinator.run(
            agent,
            enriched,
            identity_verified=True,
        )
