"""Agent that proposes an internal booking-confirmation email draft."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class NotificationDraftAgent(BaseAgent):
    """Requests a booking-bound email draft without sending it."""

    def __init__(self) -> None:
        super().__init__("Notification Draft Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        draft_id = str(context.get("draft_id", "")).strip()
        booking_id = str(context.get("booking_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        template = str(context.get("template", "booking-confirmation")).strip()

        if not draft_id or not booking_id or not job_id:
            raise ValueError("draft_id, booking_id, and job_id are required")
        if job_status != "scheduled":
            raise ValueError("job must be scheduled")
        if template != "booking-confirmation":
            raise ValueError("unsupported notification template")

        intent = BusinessIntent(
            route="notification-draft",
            action="create-booking-confirmation-draft",
            subject_id=job_id,
            parameters={
                "draft_id": draft_id,
                "booking_id": booking_id,
                "job_id": job_id,
                "job_status": job_status,
                "template": template,
                "channel": "email",
            },
            risk_level=RiskLevel.MEDIUM,
            approval_mode=ApprovalMode.HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale="A stored booking is ready to become an internal confirmation-email draft.",
            confidence=0.99,
        )
