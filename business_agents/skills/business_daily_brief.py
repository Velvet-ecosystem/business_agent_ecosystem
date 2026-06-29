"""Read-only current operational brief for the business."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from business_agents.contracts import ApprovalMode
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


_ATTENTION_STATUSES = {
    JobStatus.INTAKE_REVIEW,
    JobStatus.APPROVED,
    JobStatus.ESTIMATING,
    JobStatus.READY_TO_SCHEDULE,
}
_TERMINAL_STATUSES = {JobStatus.COMPLETED, JobStatus.CANCELLED}


class BusinessDailyBriefSkill(BaseSkill):
    """Summarize current work without claiming unsupported time-based changes."""

    contract = SkillContract(
        skill_id="business-daily-brief",
        version="1.0.0",
        domain=SkillDomain.BUSINESS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=(),
        output_fields=(
            "scope",
            "total_jobs",
            "active_jobs",
            "terminal_jobs",
            "status_counts",
            "attention_jobs",
        ),
        external_action=False,
        receipt_required=False,
        failure_behavior="fail-closed",
        cancellation_behavior="stop-immediately",
        retry_behavior="safe-read-retry",
    )

    def __init__(self, job_store: JsonlJobStore) -> None:
        self._job_store = job_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if inputs:
            raise ValueError("business-daily-brief accepts no inputs")

        records = self._job_store.list_current()
        counts = Counter(record.status.value for record in records)
        attention_jobs = tuple(
            {"job_id": record.job_id, "status": record.status.value}
            for record in records
            if record.status in _ATTENTION_STATUSES
        )
        terminal_jobs = sum(record.status in _TERMINAL_STATUSES for record in records)

        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "scope": "current-snapshot",
                "total_jobs": len(records),
                "active_jobs": len(records) - terminal_jobs,
                "terminal_jobs": terminal_jobs,
                "status_counts": dict(sorted(counts.items())),
                "attention_jobs": attention_jobs,
            },
        )
