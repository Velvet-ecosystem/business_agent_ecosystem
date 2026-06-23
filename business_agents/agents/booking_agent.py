"""Agent that proposes one real calendar booking from a stored preparation."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class BookingAgent(BaseAgent):
    """Proposes an external calendar write for one prepared window."""

    def __init__(self) -> None:
        super().__init__("Booking Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        booking_id = str(context.get("booking_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        preparation_id = str(context.get("preparation_id", "")).strip()
        idempotency_key = str(context.get("idempotency_key", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        title = str(context.get("title", "")).strip()
        description = str(context.get("description", "")).strip()

        if not all((booking_id, job_id, preparation_id, idempotency_key, title)):
            raise ValueError(
                "booking_id, job_id, preparation_id, idempotency_key, and title are required"
            )
        if job_status != "ready-to-schedule":
            raise ValueError("job must be ready-to-schedule")
        if len(title) > 200:
            raise ValueError("title is too long")
        if len(description) > 4000:
            raise ValueError("description is too long")

        intent = BusinessIntent(
            route="calendar-booking",
            action="create-calendar-booking",
            subject_id=job_id,
            parameters={
                "booking_id": booking_id,
                "job_id": job_id,
                "preparation_id": preparation_id,
                "idempotency_key": idempotency_key,
                "job_status": job_status,
                "title": title,
                "description": description,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=(
                f"Prepared window {preparation_id} is proposed for one idempotent "
                "external calendar booking."
            ),
            confidence=0.99,
        )
