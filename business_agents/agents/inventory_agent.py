"""Inventory agent for low-stock observations and restock proposals."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, BusinessIntent


class InventoryAgent(BaseAgent):
    """Produces internal restock-review proposals from bounded stock context."""

    def __init__(self) -> None:
        super().__init__("Inventory Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        sku = str(context.get("sku", "")).strip()
        location = str(context.get("location", "")).strip()
        on_hand = int(context.get("on_hand", 0))
        reorder_point = int(context.get("reorder_point", 0))
        suggested_quantity = int(context.get("suggested_quantity", 0))

        if not sku or not location:
            raise ValueError("sku and location are required")
        if min(on_hand, reorder_point, suggested_quantity) < 0:
            raise ValueError("inventory values must be non-negative")
        if on_hand >= reorder_point:
            raise ValueError("stock is not below the reorder point")
        if suggested_quantity <= 0:
            raise ValueError("suggested_quantity must be positive")

        confidence = min(1.0, 0.75 + ((reorder_point - on_hand) / max(reorder_point, 1)) * 0.25)
        intent = BusinessIntent(
            route="internal-task",
            action="create-restock-review",
            subject_id=location,
            parameters={
                "sku": sku,
                "on_hand": on_hand,
                "reorder_point": reorder_point,
                "suggested_quantity": suggested_quantity,
            },
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"{sku} is below its configured reorder point at {location}.",
            confidence=confidence,
        )
