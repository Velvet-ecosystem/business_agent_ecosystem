"""Customer intake agent for bounded internal review proposals."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, BusinessIntent


class IntakeAgent(BaseAgent):
    """Captures a customer request and proposes an internal review task only."""

    def __init__(self) -> None:
        super().__init__("Intake Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        customer_name = str(context.get("customer_name", "")).strip()
        contact = str(context.get("contact", "")).strip()
        request = str(context.get("request", "")).strip()
        source = str(context.get("source", "manual")).strip() or "manual"
        subject_id = str(context.get("subject_id", "")).strip()

        if not customer_name:
            raise ValueError("customer_name is required")
        if not contact:
            raise ValueError("contact is required")
        if not request:
            raise ValueError("request is required")
        if len(customer_name) > 120:
            raise ValueError("customer_name is too long")
        if len(contact) > 254:
            raise ValueError("contact is too long")
        if len(request) > 2000:
            raise ValueError("request is too long")
        if len(source) > 80:
            raise ValueError("source is too long")

        normalized_subject = subject_id or f"lead:{customer_name.casefold().replace(' ', '-')[:64]}"
        intent = BusinessIntent(
            route="internal-task",
            action="create-intake-review",
            subject_id=normalized_subject,
            parameters={
                "customer_name": customer_name,
                "contact": contact,
                "request": request,
                "source": source,
            },
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale="A new customer request requires internal review before any reply, quote, or booking.",
            confidence=0.9,
        )
