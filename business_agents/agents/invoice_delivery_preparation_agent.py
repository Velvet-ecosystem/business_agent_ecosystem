"""Agent that proposes preparing a finalized invoice for reviewable handoff."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class InvoiceDeliveryPreparationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Invoice Delivery Preparation Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        preparation_id = str(context.get("preparation_id", "")).strip()
        finalization_id = str(context.get("finalization_id", "")).strip()
        invoice_id = str(context.get("invoice_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        prepared_by = str(context.get("_principal_id", "")).strip()
        if not all((preparation_id, finalization_id, invoice_id, job_id, prepared_by)):
            raise ValueError("preparation_id, finalization_id, invoice_id, job_id, and verified principal are required")
        intent = BusinessIntent(
            route="invoice-delivery-preparation",
            action="prepare-invoice-delivery",
            subject_id=job_id,
            parameters={
                "preparation_id": preparation_id,
                "finalization_id": finalization_id,
                "invoice_id": invoice_id,
                "job_id": job_id,
                "prepared_by": prepared_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Finalized invoice {invoice_id} is proposed for local delivery preparation.",
            confidence=0.99,
        )
