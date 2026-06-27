"""Agent that proposes finalizing an existing local invoice draft."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class InvoiceFinalizationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Invoice Finalization Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        finalization_id = str(context.get("finalization_id", "")).strip()
        invoice_id = str(context.get("invoice_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        approved_by = str(context.get("_principal_id", "")).strip()
        if not all((finalization_id, invoice_id, job_id, approved_by)):
            raise ValueError("finalization_id, invoice_id, job_id, and verified principal are required")
        intent = BusinessIntent(
            route="invoice-finalization",
            action="finalize-invoice",
            subject_id=job_id,
            parameters={
                "finalization_id": finalization_id,
                "invoice_id": invoice_id,
                "job_id": job_id,
                "approved_by": approved_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Invoice draft {invoice_id} is proposed for finalization.",
            confidence=0.99,
        )
