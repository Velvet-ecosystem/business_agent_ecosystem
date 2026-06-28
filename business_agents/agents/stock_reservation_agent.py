"""Agent that proposes a stock reservation record."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class StockReservationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Stock Reservation Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        reservation_id = str(context.get("reservation_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        item_reference = str(context.get("item_reference", "")).strip()
        quantity_reference = str(context.get("quantity_reference", "")).strip()
        location_reference = str(context.get("location_reference", "")).strip()
        reserved_by = str(context.get("_principal_id", "")).strip()
        if not all((reservation_id, job_id, item_reference, quantity_reference, location_reference, reserved_by)):
            raise ValueError("reservation fields and verified principal are required")
        intent = BusinessIntent(
            route="stock-reservation",
            action="record-stock-reservation",
            subject_id=job_id,
            parameters={
                "reservation_id": reservation_id,
                "job_id": job_id,
                "item_reference": item_reference,
                "quantity_reference": quantity_reference,
                "location_reference": location_reference,
                "reserved_by": reserved_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Stock reservation {reservation_id} is proposed for job {job_id}.",
            confidence=0.99,
        )
