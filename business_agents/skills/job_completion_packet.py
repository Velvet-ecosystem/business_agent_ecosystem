"""Read-only internal packet assembled from completed job evidence."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.completion_evidence import CompletionEvidenceStore
from business_agents.contracts import ApprovalMode
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class JobCompletionPacketSkill(BaseSkill):
    """Assemble an internal completion packet without exporting or sending it."""

    contract = SkillContract(
        skill_id="job-completion-packet",
        version="1.0.0",
        domain=SkillDomain.BUSINESS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=("job_id",),
        output_fields=("packet", "delivery_authority"),
        external_action=False,
        receipt_required=False,
        artifact_types=("internal-completion-packet",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-immediately",
        retry_behavior="safe-read-retry",
    )

    def __init__(self, job_store: JsonlJobStore, evidence_store: CompletionEvidenceStore) -> None:
        self._job_store = job_store
        self._evidence_store = evidence_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if set(inputs) != {"job_id"}:
            raise ValueError("job-completion-packet requires only job_id")
        job_id = inputs["job_id"]
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string")

        job = self._job_store.get(job_id)
        if job is None:
            raise ValueError("job not found")
        if job.status is not JobStatus.COMPLETED:
            raise ValueError("job must be completed")

        evidence = self._evidence_store.get_by_job(job_id)
        if evidence is None:
            raise ValueError("completion evidence not found")

        packet = {
            "job_id": job.job_id,
            "status": job.status.value,
            "evidence_id": evidence.evidence_id,
            "completed_by": evidence.completed_by,
            "summary": evidence.summary,
            "checklist": evidence.checklist,
            "artifact_refs": evidence.artifact_refs,
            "customer_acknowledged": evidence.customer_acknowledged,
        }
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={"packet": packet, "delivery_authority": False},
            artifacts=("internal-completion-packet",),
        )
