"""Agent that proposes moving an estimating job to ready-to-schedule."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class EstimateReadinessAgent(BaseAgent):
    """Requires an estimate reference before proposing scheduling readiness."""

    def __init__(self) -> None:
        super().__init__("Estimate Readiness Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        job_id = str(context.get("job_id", "")).strip()
        estimate_id = str(context.get("estimate_id", "")).strip()
        current_status = str(context.get("current_status", "")).strip()
        reason = str(context.get("reason", "")).strip()

        if not job_id or not estimate_id or not reason:
            raise ValueError("job_id, estimate_id, and reason are required")
        if current_status != "estimating":
            raise ValueError("job must be in estimating status")
        if len(reason) > 1000:
            raise ValueError("reason is too long")

        intent = BusinessIntent(
            route="estimate-readiness",
            action="mark-ready-to-schedule",
            subject_id=job_id,
            parameters={
                "job_id": job_id,
                "estimate_id": estimate_id,
                "current_status": current_status,
                "target_status": "ready-to-schedule",
                "reason": reason,
            },
            risk_level=RiskLevel.MEDIUM,
            approval_mode=ApprovalMode.HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=(
                f"Job {job_id} has an estimate reference and is proposed to move "
                "from estimating to ready-to-schedule."
            ),
            confidence=0.99,
        )
