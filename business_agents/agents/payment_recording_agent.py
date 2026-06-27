"""Agent that proposes recording a reported payment against an invoice."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel
from business_agents.estimates import money


class PaymentRecordingAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Payment Recording Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        payment_id = str(context.get("payment_id", "")).strip()
        invoice_id = str(context.get("invoice_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        handoff_confirmation_id = str(context.get("handoff_confirmation_id", "")).strip()
        currency = str(context.get("currency", "")).strip().upper()
        source_reference = str(context.get("source_reference", "")).strip()
        recorded_by = str(context.get("_principal_id", "")).strip()
        amount = money(context.get("amount", "0"))
        if not all((payment_id, invoice_id, job_id, handoff_confirmation_id, currency, source_reference, recorded_by)):
            raise ValueError("payment fields and verified principal are required")
        if amount <= 0:
            raise ValueError("amount must be positive")
        intent = BusinessIntent(
            route="payment-recording",
            action="record-reported-payment",
            subject_id=job_id,
            parameters={
                "payment_id": payment_id,
                "invoice_id": invoice_id,
                "job_id": job_id,
                "handoff_confirmation_id": handoff_confirmation_id,
                "amount": str(amount),
                "currency": currency,
                "source_reference": source_reference,
                "recorded_by": recorded_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Reported payment {payment_id} is proposed for recording against invoice {invoice_id}.",
            confidence=0.99,
        )
