"""Agent that proposes creation of an internal durable job record."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class JobAgent(BaseAgent):
    """Turns approved intake context into a job-record creation proposal."""

    def __init__(self) -> None:
        super().__init__("Job Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        customer_name = str(context.get("customer_name", "")).strip()
        contact = str(context.get("contact", "")).strip()
        request = str(context.get("request", "")).strip()
        source = str(context.get("source", "manual")).strip() or "manual"
        intake_task_id = str(context.get("intake_task_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()

        if not all((customer_name, contact, request, intake_task_id, job_id)):
            raise ValueError(
                "customer_name, contact, request, intake_task_id, and job_id are required"
            )

        intent = BusinessIntent(
            route="job-record",
            action="create-job",
            subject_id=job_id,
            parameters={
                "job_id": job_id,
                "customer_name": customer_name,
                "contact": contact,
                "request": request,
                "source": source,
                "intake_task_id": intake_task_id,
            },
            risk_level=RiskLevel.MEDIUM,
            approval_mode=ApprovalMode.HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale="An approved intake review is ready to become a durable internal job record.",
            confidence=0.95,
        )
