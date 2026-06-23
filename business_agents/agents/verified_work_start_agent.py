"""Work-start proposal that derives the actor from verified principal context."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.work_start_agent import WorkStartAgent
from business_agents.contracts import AgentProposal


class VerifiedWorkStartAgent(WorkStartAgent):
    """Ignores caller-supplied actor names and uses verified principal identity."""

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        principal_id = str(context.get("_principal_id", "")).strip()
        display_name = str(context.get("_principal_display_name", "")).strip()
        if not principal_id or not display_name:
            raise PermissionError("verified-principal-context-required")

        secured = dict(context)
        secured["started_by"] = principal_id
        proposal = super().propose(secured)
        return AgentProposal(
            agent_name=proposal.agent_name,
            intent=proposal.intent,
            rationale=(
                f"Verified principal {display_name} ({principal_id}) is starting "
                f"scheduled job {proposal.intent.subject_id}."
            ),
            confidence=proposal.confidence,
        )
