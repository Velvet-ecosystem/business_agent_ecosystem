"""Agent that proposes one explicit job lifecycle transition."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel
from business_agents.jobs import JobStatus


class JobTransitionAgent(BaseAgent):
    """Proposes a single, human-approved transition for an existing job."""

    def __init__(self) -> None:
        super().__init__("Job Transition Agent")

    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        job_id = str(context.get("job_id", "")).strip()
        current_status_raw = str(context.get("current_status", "")).strip()
        target_status_raw = str(context.get("target_status", "")).strip()
        reason = str(context.get("reason", "")).strip()

        if not job_id or not current_status_raw or not target_status_raw or not reason:
            raise ValueError("job_id, current_status, target_status, and reason are required")
        if len(reason) > 1000:
            raise ValueError("reason is too long")

        try:
            current_status = JobStatus(current_status_raw)
            target_status = JobStatus(target_status_raw)
        except ValueError as exc:
            raise ValueError("unsupported job status") from exc

        risk = RiskLevel.HIGH if target_status in {JobStatus.COMPLETED, JobStatus.CANCELLED} else RiskLevel.MEDIUM
        approval = ApprovalMode.STRONG_HUMAN if risk is RiskLevel.HIGH else ApprovalMode.HUMAN

        intent = BusinessIntent(
            route="job-transition",
            action="transition-job",
            subject_id=job_id,
            parameters={
                "job_id": job_id,
                "current_status": current_status.value,
                "target_status": target_status.value,
                "reason": reason,
            },
            risk_level=risk,
            approval_mode=approval,
        )
        return AgentProposal(
            agent_name=self.name,
            intent=intent,
            rationale=(
                f"Job {job_id} is proposed to move from {current_status.value} "
                f"to {target_status.value}."
            ),
            confidence=0.99,
        )
