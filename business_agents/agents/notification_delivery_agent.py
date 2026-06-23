"""Agent that proposes delivery of one stored notification draft."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class NotificationDeliveryAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Notification Delivery Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        delivery_id = str(context.get("delivery_id", "")).strip()
        draft_id = str(context.get("draft_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        idempotency_key = str(context.get("idempotency_key", "")).strip()
        job_status = str(context.get("job_status", "")).strip()

        if not all((delivery_id, draft_id, job_id, idempotency_key)):
            raise ValueError("delivery_id, draft_id, job_id, and idempotency_key are required")
        if job_status != "scheduled":
            raise ValueError("job must be scheduled")

        intent = BusinessIntent(
            route="notification-delivery",
            action="deliver-notification-draft",
            subject_id=job_id,
            parameters={
                "delivery_id": delivery_id,
                "draft_id": draft_id,
                "job_id": job_id,
                "idempotency_key": idempotency_key,
                "job_status": job_status,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale="A stored notification draft is proposed for one idempotent external delivery.",
            confidence=0.99,
        )
