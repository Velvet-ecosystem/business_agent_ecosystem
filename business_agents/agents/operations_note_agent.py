"""Agent for proposing bounded internal operations notes."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, BusinessIntent


class OperationsNoteAgent(BaseAgent):
    """Turns local operations context into a note proposal."""

    def __init__(self) -> None:
        super().__init__("Operations Note Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        subject_id = str(context.get("subject_id", "")).strip()
        title = str(context.get("title", "")).strip()
        body = str(context.get("body", "")).strip()

        if not subject_id:
            raise ValueError("subject_id is required")
        if not title:
            raise ValueError("title is required")
        if not body:
            raise ValueError("body is required")

        intent = BusinessIntent(
            route="internal-note",
            action="record-operations-note",
            subject_id=subject_id,
            parameters={"title": title, "body": body},
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale="The operations context should be preserved as a local internal note.",
            confidence=0.9,
        )
