"""Agent that proposes a local invoice draft for completed work."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel
from business_agents.estimates import money


class InvoiceDraftAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Invoice Draft Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        invoice_id = str(context.get("invoice_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        evidence_id = str(context.get("evidence_id", "")).strip()
        currency = str(context.get("currency", "")).strip().upper()
        notes = str(context.get("notes", "")).strip()
        subtotal = money(context.get("subtotal", "0"))
        tax_rate = Decimal(str(context.get("tax_rate", "0")))
        if not all((invoice_id, job_id, evidence_id, currency)):
            raise ValueError("invoice_id, job_id, evidence_id, and currency are required")
        if job_status != "completed":
            raise ValueError("job must be completed")
        if tax_rate < 0 or tax_rate > 1:
            raise ValueError("tax_rate must be between 0 and 1")
        tax_amount = money(subtotal * tax_rate)
        total = money(subtotal + tax_amount)
        intent = BusinessIntent(
            route="invoice-draft",
            action="create-invoice-draft",
            subject_id=job_id,
            parameters={
                "invoice_id": invoice_id,
                "job_id": job_id,
                "job_status": job_status,
                "evidence_id": evidence_id,
                "currency": currency,
                "subtotal": str(subtotal),
                "tax_amount": str(tax_amount),
                "total": str(total),
                "notes": notes,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Completed job {job_id} has a local invoice draft proposed for review.",
            confidence=0.99,
        )
