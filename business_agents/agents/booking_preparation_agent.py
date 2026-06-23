"""Agent that proposes preparation of one selected schedule window."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class BookingPreparationAgent(BaseAgent):
    """Selects one candidate by index without creating a real booking."""

    def __init__(self) -> None:
        super().__init__("Booking Preparation Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        job_id = str(context.get("job_id", "")).strip()
        proposal_id = str(context.get("proposal_id", "")).strip()
        preparation_id = str(context.get("preparation_id", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        notes = str(context.get("notes", "")).strip()
        selected_index = context.get("selected_index")

        if not job_id or not proposal_id or not preparation_id:
            raise ValueError("job_id, proposal_id, and preparation_id are required")
        if job_status != "ready-to-schedule":
            raise ValueError("job must be ready-to-schedule")
        if not isinstance(selected_index, int) or isinstance(selected_index, bool):
            raise ValueError("selected_index must be an integer")
        if selected_index < 0:
            raise ValueError("selected_index must be non-negative")
        if len(notes) > 2000:
            raise ValueError("notes are too long")

        intent = BusinessIntent(
            route="booking-preparation",
            action="prepare-selected-window",
            subject_id=job_id,
            parameters={
                "preparation_id": preparation_id,
                "proposal_id": proposal_id,
                "job_id": job_id,
                "job_status": job_status,
                "selected_index": selected_index,
                "notes": notes,
            },
            risk_level=RiskLevel.MEDIUM,
            approval_mode=ApprovalMode.HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=(
                f"Candidate window {selected_index} from schedule proposal {proposal_id} "
                "is selected for internal booking preparation only."
            ),
            confidence=0.99,
        )
