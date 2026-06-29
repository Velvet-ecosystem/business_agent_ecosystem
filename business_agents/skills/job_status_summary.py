"""Read-only summary of current job states."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from business_agents.contracts import ApprovalMode
from business_agents.jobs import JsonlJobStore
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class JobStatusSummarySkill(BaseSkill):
    contract = SkillContract(
        skill_id="job-status-summary",
        version="1.0.0",
        domain=SkillDomain.BUSINESS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=(),
        output_fields=("total_jobs", "status_counts", "jobs"),
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
            raise ValueError("job-status-summary accepts no inputs")

        records = self._job_store.list_current()
        counts = Counter(record.status.value for record in records)
        jobs = tuple(
            {"job_id": record.job_id, "status": record.status.value}
            for record in records
        )
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "total_jobs": len(records),
                "status_counts": dict(sorted(counts.items())),
                "jobs": jobs,
            },
        )
