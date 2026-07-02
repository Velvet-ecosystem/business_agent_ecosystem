"""Record an explicit human approval decision without granting authority."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.approval_decisions import (
    ApprovalDecision,
    ApprovalDecisionStore,
    ApprovalDecisionValue,
)
from business_agents.approval_requests import ApprovalRequestStatus, ApprovalRequestStore
from business_agents.contracts import ApprovalMode
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class RecordApprovalDecisionSkill(BaseSkill):
    contract = SkillContract(
        skill_id="record-approval-decision",
        version="1.0.0",
        domain=SkillDomain.OPERATIONS,
        effect=SkillEffect.STATE_CHANGING,
        approval_mode=ApprovalMode.STRONG_HUMAN,
        input_fields=(
            "decision_id",
            "request_id",
            "decision",
            "decided_by",
            "rationale",
            "strong_confirmation",
        ),
        output_fields=("decision", "court_authority", "execution_authority"),
        capability_route="approval-decision",
        capability_action="record-human-decision",
        external_action=False,
        receipt_required=False,
        artifact_types=("approval-decision",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-before-decision-write",
        retry_behavior="manual-on-duplicate",
    )

    def __init__(
        self,
        request_store: ApprovalRequestStore,
        decision_store: ApprovalDecisionStore,
    ) -> None:
        self._request_store = request_store
        self._decision_store = decision_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if set(inputs) != set(self.contract.input_fields):
            raise ValueError("record-approval-decision requires exact declared inputs")

        for name in ("decision_id", "request_id", "decision", "decided_by", "rationale"):
            value = inputs[name]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(inputs["strong_confirmation"], bool):
            raise ValueError("strong_confirmation must be a bool")

        request = next(
            (
                item
                for item in self._request_store.list_current()
                if item.request_id == inputs["request_id"]
            ),
            None,
        )
        if request is None:
            raise ValueError("approval request not found")
        if request.status is not ApprovalRequestStatus.PENDING:
            raise ValueError("approval request is not pending")

        try:
            value = ApprovalDecisionValue(inputs["decision"])
        except ValueError as exc:
            raise ValueError("decision must be approve or deny") from exc

        if value is ApprovalDecisionValue.APPROVE and request.approval_mode is ApprovalMode.STRONG_HUMAN:
            if not inputs["strong_confirmation"]:
                raise ValueError("strong confirmation is required for approval")

        decision = ApprovalDecision(
            decision_id=inputs["decision_id"],
            request_id=request.request_id,
            decision=value,
            decided_by=inputs["decided_by"],
            rationale=inputs["rationale"],
            strong_confirmation=inputs["strong_confirmation"],
        )
        self._decision_store.create(decision)

        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "decision": {
                    "decision_id": decision.decision_id,
                    "request_id": decision.request_id,
                    "decision": decision.decision.value,
                    "decided_by": decision.decided_by,
                    "rationale": decision.rationale,
                    "strong_confirmation": decision.strong_confirmation,
                },
                "court_authority": False,
                "execution_authority": False,
            },
            artifacts=("approval-decision",),
        )
