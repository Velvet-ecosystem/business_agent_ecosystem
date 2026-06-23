"""Strict principal-aware execution wrapper."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import ExecutorResult
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.identity import VerifiedPrincipal


class VerifiedBusinessCoordinator:
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
        if not principal.is_fresh(max_age_seconds=self.max_age_seconds):
            raise PermissionError("identity-stale")

        enriched = dict(context)
        enriched["_principal_id"] = principal.principal_id
        enriched["_principal_display_name"] = principal.display_name
        enriched["_principal_role"] = principal.role
        enriched["_principal_session_id"] = principal.session_id
        enriched["_principal_presence_level"] = principal.presence_level.value
        enriched["_principal_verified_at"] = principal.verified_at

        result = self.coordinator.run(agent, enriched, identity_verified=True)
        self.coordinator.receipt_store.append(
            actor="Verified Principal",
            decision="actor-bound",
            executor=result.executor_name,
            subject_id=str(result.output.get("job_id", "unknown")),
            details={
                **principal.receipt_details(),
                "result_receipt_id": result.receipt_id,
                "executor_status": result.status,
            },
        )
        return result
