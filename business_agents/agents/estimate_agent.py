"""Agent that proposes creation of an internal estimate draft."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel
from business_agents.estimates import money


class EstimateAgent(BaseAgent):
    """Calculates a bounded internal estimate draft for an estimating job."""

    def __init__(self) -> None:
        super().__init__("Estimate Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        job_id = str(context.get("job_id", "")).strip()
        estimate_id = str(context.get("estimate_id", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        currency = str(context.get("currency", "CAD")).strip().upper()
        notes = str(context.get("notes", "")).strip()

        if not job_id or not estimate_id:
            raise ValueError("job_id and estimate_id are required")
        if job_status != "estimating":
            raise ValueError("job must be in estimating status")
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        if len(notes) > 2000:
            raise ValueError("notes are too long")

        labour_hours = self._decimal(context.get("labour_hours", 0), "labour_hours")
        labour_rate = money(context.get("labour_rate", 0))
        materials_subtotal = money(context.get("materials_subtotal", 0))
        contingency_rate = self._rate(context.get("contingency_rate", 0), "contingency_rate")
        margin_rate = self._rate(context.get("margin_rate", 0), "margin_rate")
        tax_rate = self._rate(context.get("tax_rate", 0), "tax_rate")

        labour_subtotal = money(labour_hours * labour_rate)
        direct_cost = labour_subtotal + materials_subtotal
        contingency_amount = money(direct_cost * contingency_rate)
        pre_margin = direct_cost + contingency_amount
        margin_amount = money(pre_margin * margin_rate)
        pre_tax = pre_margin + margin_amount
        tax_amount = money(pre_tax * tax_rate)
        total = money(pre_tax + tax_amount)

        intent = BusinessIntent(
            route="estimate-draft",
            action="create-estimate-draft",
            subject_id=job_id,
            parameters={
                "estimate_id": estimate_id,
                "job_id": job_id,
                "job_status": job_status,
                "currency": currency,
                "labour_hours": str(labour_hours),
                "labour_rate": str(labour_rate),
                "labour_subtotal": str(labour_subtotal),
                "materials_subtotal": str(materials_subtotal),
                "contingency_rate": str(contingency_rate),
                "contingency_amount": str(contingency_amount),
                "margin_rate": str(margin_rate),
                "margin_amount": str(margin_amount),
                "tax_rate": str(tax_rate),
                "tax_amount": str(tax_amount),
                "total": str(total),
                "notes": notes,
            },
            risk_level=RiskLevel.MEDIUM,
            approval_mode=ApprovalMode.HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale="The estimating job has enough bounded pricing inputs to prepare an internal draft.",
            confidence=0.95,
        )

    @staticmethod
    def _decimal(value: object, name: str) -> Decimal:
        try:
            result = Decimal(str(value))
        except Exception as exc:
            raise ValueError(f"{name} must be numeric") from exc
        if not result.is_finite() or result < 0:
            raise ValueError(f"{name} must be finite and non-negative")
        return result

    @classmethod
    def _rate(cls, value: object, name: str) -> Decimal:
        result = cls._decimal(value, name)
        if result > Decimal("1"):
            raise ValueError(f"{name} must be between 0 and 1")
        return result
