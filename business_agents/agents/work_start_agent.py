"""Agent that proposes beginning work on a scheduled job."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class WorkStartAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Work Start Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        start_id = str(context.get("start_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        booking_id = str(context.get("booking_id", "")).strip()
        started_by = str(context.get("started_by", "")).strip()
        reason = str(context.get("reason", "")).strip()
        job_status = str(context.get("job_status", "")).strip()

        if not all((start_id, job_id, booking_id, started_by, reason)):
            raise ValueError("start_id, job_id, booking_id, started_by, and reason are required")
        if job_status != "scheduled":
            raise ValueError("job must be scheduled")
        if len(reason) > 2000:
            raise ValueError("reason is too long")

        intent = BusinessIntent(
            route="work-start",
            action="start-work",
            subject_id=job_id,
            parameters={
                "start_id": start_id,
                "job_id": job_id,
                "booking_id": booking_id,
                "started_by": started_by,
                "reason": reason,
                "job_status": job_status,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Scheduled job {job_id} is proposed to enter active work.",
            confidence=0.99,
        )
