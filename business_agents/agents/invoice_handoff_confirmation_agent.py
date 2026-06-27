"""Agent that proposes confirming an authorized invoice handoff."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class InvoiceHandoffConfirmationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Invoice Handoff Confirmation Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        confirmation_id = str(context.get("confirmation_id", "")).strip()
        preparation_id = str(context.get("preparation_id", "")).strip()
        invoice_id = str(context.get("invoice_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        channel_reference = str(context.get("channel_reference", "")).strip()
        recipient_reference = str(context.get("recipient_reference", "")).strip()
        confirmed_by = str(context.get("_principal_id", "")).strip()
        if not all((confirmation_id, preparation_id, invoice_id, job_id, channel_reference, recipient_reference, confirmed_by)):
            raise ValueError("confirmation fields and verified principal are required")
        intent = BusinessIntent(
            route="invoice-handoff-confirmation",
            action="confirm-invoice-handoff",
            subject_id=job_id,
            parameters={
                "confirmation_id": confirmation_id,
                "preparation_id": preparation_id,
                "invoice_id": invoice_id,
                "job_id": job_id,
                "channel_reference": channel_reference,
                "recipient_reference": recipient_reference,
                "confirmed_by": confirmed_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Invoice {invoice_id} handoff is proposed for confirmation.",
            confidence=0.99,
        )
