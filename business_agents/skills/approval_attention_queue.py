"""Read-only summary of work awaiting explicit approval."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from business_agents.approval_requests import ApprovalRequestStore
from business_agents.contracts import ApprovalMode
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class ApprovalAttentionQueueSkill(BaseSkill):
    contract = SkillContract(
        skill_id="approval-attention-queue",
        version="1.0.0",
        domain=SkillDomain.OPERATIONS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=(),
        output_fields=("pending_count", "risk_counts", "approval_mode_counts", "requests"),
        external_action=False,
        receipt_required=False,
        failure_behavior="fail-closed",
        cancellation_behavior="stop-immediately",
        retry_behavior="safe-read-retry",
    )

    def __init__(self, approval_store: ApprovalRequestStore) -> None:
        self._approval_store = approval_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if inputs:
            raise ValueError("approval-attention-queue accepts no inputs")

        pending = self._approval_store.list_pending()
        risk_counts = Counter(request.risk_level.value for request in pending)
        mode_counts = Counter(request.approval_mode.value for request in pending)
        requests = tuple(
            {
                "request_id": request.request_id,
                "route": request.route,
                "action": request.action,
                "subject_id": request.subject_id,
                "summary": request.summary,
                "risk_level": request.risk_level.value,
                "approval_mode": request.approval_mode.value,
            }
            for request in pending
        )
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "pending_count": len(pending),
                "risk_counts": dict(sorted(risk_counts.items())),
                "approval_mode_counts": dict(sorted(mode_counts.items())),
                "requests": requests,
            },
        )
