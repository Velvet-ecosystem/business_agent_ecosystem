"""Agent that proposes creating a customer account and binding it to a job."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class CustomerAccountBindingAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Customer Account Binding Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        customer_id = str(context.get("customer_id", "")).strip()
        display_name = str(context.get("display_name", "")).strip()
        contact_reference = str(context.get("primary_contact_reference", "")).strip()
        binding_id = str(context.get("binding_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        bound_by = str(context.get("_principal_id", "")).strip()
        if not all((customer_id, display_name, contact_reference, binding_id, job_id, bound_by)):
            raise ValueError("customer account fields and verified principal are required")
        intent = BusinessIntent(
            route="customer-account-binding",
            action="create-and-bind-customer",
            subject_id=job_id,
            parameters={
                "customer_id": customer_id,
                "display_name": display_name,
                "primary_contact_reference": contact_reference,
                "binding_id": binding_id,
                "job_id": job_id,
                "bound_by": bound_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Customer account {customer_id} is proposed for binding to job {job_id}.",
            confidence=0.99,
        )
