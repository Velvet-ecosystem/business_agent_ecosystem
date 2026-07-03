"""Read-only summary of approval work with derived current decision state."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from business_agents.approval_decisions import ApprovalDecisionStore
from business_agents.approval_requests import ApprovalRequestStore
from business_agents.contracts import ApprovalMode
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class ApprovalAttentionQueueSkill(BaseSkill):
    contract = SkillContract(
        skill_id="approval-attention-queue",
        version="2.0.0",
        domain=SkillDomain.OPERATIONS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=(),
        output_fields=(
            "pending_count",
            "decided_count",
            "state_counts",
            "risk_counts",
            "approval_mode_counts",
            "requests",
        ),
        external_action=False,
        receipt_required=False,
        failure_behavior="fail-closed",
        cancellation_behavior="stop-immediately",
        retry_behavior="safe-read-retry",
    )

    def __init__(
        self,
        approval_store: ApprovalRequestStore,
        decision_store: ApprovalDecisionStore,
    ) -> None:
        self._approval_store = approval_store
        self._decision_store = decision_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if inputs:
            raise ValueError("approval-attention-queue accepts no inputs")

        current = []
        for request in self._approval_store.list_current():
            decision = self._decision_store.get_for_request(request.request_id)
            state = "pending" if decision is None else decision.decision.value
            current.append((request, decision, state))

        pending = tuple(item for item in current if item[2] == "pending")
        decided = tuple(item for item in current if item[2] != "pending")
        risk_counts = Counter(request.risk_level.value for request, _, _ in pending)
        mode_counts = Counter(request.approval_mode.value for request, _, _ in pending)
        state_counts = Counter(state for _, _, state in current)
        requests = tuple(
            {
                "request_id": request.request_id,
                "route": request.route,
                "action": request.action,
                "subject_id": request.subject_id,
                "summary": request.summary,
                "risk_level": request.risk_level.value,
                "approval_mode": request.approval_mode.value,
                "review_state": state,
                "decision_id": decision.decision_id if decision else None,
            }
            for request, decision, state in sorted(current, key=lambda item: item[0].request_id)
        )
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "pending_count": len(pending),
                "decided_count": len(decided),
                "state_counts": dict(sorted(state_counts.items())),
                "risk_counts": dict(sorted(risk_counts.items())),
                "approval_mode_counts": dict(sorted(mode_counts.items())),
                "requests": requests,
            },
        )
