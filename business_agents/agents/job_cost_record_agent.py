"""Agent that proposes a job cost reference record."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class JobCostRecordAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Job Cost Record Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        record_id = str(context.get("record_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        category = str(context.get("category", "")).strip()
        description = str(context.get("description", "")).strip()
        amount_reference = str(context.get("amount_reference", "")).strip()
        evidence_reference = str(context.get("evidence_reference", "")).strip()
        recorded_by = str(context.get("_principal_id", "")).strip()
        if not all((record_id, job_id, category, description, amount_reference, evidence_reference, recorded_by)):
            raise ValueError("job cost fields and verified principal are required")
        intent = BusinessIntent(
            route="job-cost-record",
            action="record-job-cost-reference",
            subject_id=job_id,
            parameters={
                "record_id": record_id,
                "job_id": job_id,
                "category": category,
                "description": description,
                "amount_reference": amount_reference,
                "evidence_reference": evidence_reference,
                "recorded_by": recorded_by,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Job cost record {record_id} is proposed for job {job_id}.",
            confidence=0.99,
        )
