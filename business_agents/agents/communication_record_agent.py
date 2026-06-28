"""Agent that proposes an archival communication record."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class CommunicationRecordAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Communication Record Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        fields = {
            "record_id": str(context.get("record_id", "")).strip(),
            "job_id": str(context.get("job_id", "")).strip(),
            "customer_reference": str(context.get("customer_reference", "")).strip(),
            "channel": str(context.get("channel", "")).strip(),
            "direction": str(context.get("direction", "")).strip(),
            "subject_reference": str(context.get("subject_reference", "")).strip(),
            "content_reference": str(context.get("content_reference", "")).strip(),
            "recorded_by": str(context.get("_principal_id", "")).strip(),
        }
        if not all(fields.values()):
            raise ValueError("communication record fields and verified principal are required")
        intent = BusinessIntent(
            route="communication-history",
            action="record-communication-reference",
            subject_id=fields["job_id"],
            parameters=fields,
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Communication record {fields['record_id']} is proposed for job {fields['job_id']}.",
            confidence=0.99,
        )
