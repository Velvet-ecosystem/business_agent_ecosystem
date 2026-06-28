"""Agent that proposes a derived report snapshot."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class ReportSnapshotAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Report Snapshot Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        fields = {
            "report_id": str(context.get("report_id", "")).strip(),
            "report_type": str(context.get("report_type", "")).strip(),
            "scope_reference": str(context.get("scope_reference", "")).strip(),
            "source_reference": str(context.get("source_reference", "")).strip(),
            "generated_by": str(context.get("_principal_id", "")).strip(),
            "generated_at_reference": str(context.get("generated_at_reference", "")).strip(),
        }
        if not all(fields.values()):
            raise ValueError("report fields and verified principal are required")
        intent = BusinessIntent(
            route="report-snapshot",
            action="record-report-snapshot",
            subject_id=fields["scope_reference"],
            parameters=fields,
            risk_level=RiskLevel.MEDIUM,
            approval_mode=ApprovalMode.HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Derived report snapshot {fields['report_id']} is proposed.",
            confidence=0.99,
        )
