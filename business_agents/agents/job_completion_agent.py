"""Agent that proposes completing an in-progress job with exact stored evidence."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class JobCompletionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Job Completion Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        job_id = str(context.get("job_id", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        evidence_id = str(context.get("evidence_id", "")).strip()

        if not all((job_id, evidence_id)):
            raise ValueError("job_id and evidence_id are required")
        if job_status != "in-progress":
            raise ValueError("job must be in-progress")

        intent = BusinessIntent(
            route="job-completion",
            action="complete-job",
            subject_id=job_id,
            parameters={
                "job_id": job_id,
                "job_status": job_status,
                "evidence_id": evidence_id,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"In-progress job {job_id} is proposed for completion using evidence {evidence_id}.",
            confidence=0.99,
        )
