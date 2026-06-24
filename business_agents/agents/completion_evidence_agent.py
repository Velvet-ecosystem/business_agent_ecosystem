"""Agent that proposes recording completion evidence for active work."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel


class CompletionEvidenceAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Completion Evidence Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        evidence_id = str(context.get("evidence_id", "")).strip()
        job_id = str(context.get("job_id", "")).strip()
        job_status = str(context.get("job_status", "")).strip()
        completed_by = str(context.get("_principal_id", "")).strip()
        summary = str(context.get("summary", "")).strip()
        checklist_raw = context.get("checklist", ())
        artifact_refs_raw = context.get("artifact_refs", ())
        customer_acknowledged = context.get("customer_acknowledged", False)

        if not all((evidence_id, job_id, completed_by, summary)):
            raise ValueError("evidence_id, job_id, verified principal, and summary are required")
        if job_status != "in-progress":
            raise ValueError("job must be in-progress")
        if not isinstance(checklist_raw, (list, tuple)) or not checklist_raw:
            raise ValueError("checklist must contain at least one item")
        if not isinstance(artifact_refs_raw, (list, tuple)):
            raise ValueError("artifact_refs must be a list or tuple")
        if not isinstance(customer_acknowledged, bool):
            raise ValueError("customer_acknowledged must be boolean")

        checklist = tuple(str(item).strip() for item in checklist_raw)
        artifact_refs = tuple(str(item).strip() for item in artifact_refs_raw)
        if any(not item for item in checklist):
            raise ValueError("checklist items must be non-empty")
        if any(not item for item in artifact_refs):
            raise ValueError("artifact references must be non-empty")

        intent = BusinessIntent(
            route="completion-evidence",
            action="record-completion-evidence",
            subject_id=job_id,
            parameters={
                "evidence_id": evidence_id,
                "job_id": job_id,
                "job_status": job_status,
                "completed_by": completed_by,
                "summary": summary,
                "checklist": checklist,
                "artifact_refs": artifact_refs,
                "customer_acknowledged": customer_acknowledged,
            },
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=f"Active job {job_id} has proposed completion evidence for review.",
            confidence=0.99,
        )
