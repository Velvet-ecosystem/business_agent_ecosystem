"""Agent that proposes a versioned change order."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class ChangeOrderAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Change Order Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        change_order_id = str(context.get("change_order_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        reason = str(context.get("reason", "")).strip()
        scope_delta = str(context.get("scope_delta", "")).strip()
        cost_ref = str(context.get("cost_impact_reference", "")).strip()
        schedule_ref = str(context.get("schedule_impact_reference", "")).strip()
        proposed_by = str(context.get("_principal_id", "")).strip()
        try:
            version = int(context.get("version", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("version must be an integer") from exc
        if not all((change_order_id, job_id, reason, scope_delta, cost_ref, schedule_ref, proposed_by)):
            raise ValueError("change order fields and verified principal are required")
        intent = BusinessIntent(
            route="change-order",
            action="record-change-order",
            subject_id=job_id,
            parameters={
                "change_order_id": change_order_id,
                "job_id": job_id,
                "version": str(version),
                "reason": reason,
                "scope_delta": scope_delta,
                "cost_impact_reference": cost_ref,
                "schedule_impact_reference": schedule_ref,
                "proposed_by": proposed_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Version {version} change order is proposed for job {job_id}.",
            confidence=0.99,
        )
