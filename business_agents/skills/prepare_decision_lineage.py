"""Prepare a bounded lineage package from an approved human decision."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.approval_decisions import ApprovalDecisionStore, ApprovalDecisionValue
from business_agents.approval_requests import ApprovalRequestStore
from business_agents.contracts import ApprovalMode
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class PrepareDecisionLineageSkill(BaseSkill):
    contract = SkillContract(
        skill_id="prepare-decision-lineage",
        version="1.0.0",
        domain=SkillDomain.PROTECTIVE,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.STRONG_HUMAN,
        input_fields=("request_id",),
        output_fields=("lineage_package", "authority_granted", "action_performed"),
        external_action=False,
        receipt_required=False,
        artifact_types=("decision-lineage-package",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-before-handoff",
        retry_behavior="safe-preparation-retry",
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
        if set(inputs) != {"request_id"}:
            raise ValueError("prepare-decision-lineage requires only request_id")
        request_id = inputs["request_id"]
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("request_id must be a non-empty string")

        request = next(
            (item for item in self._request_store.list_current() if item.request_id == request_id),
            None,
        )
        if request is None:
            raise ValueError("approval request not found")

        decision = self._decision_store.get_for_request(request_id)
        if decision is None:
            raise ValueError("approval decision not found")
        if decision.decision is not ApprovalDecisionValue.APPROVE:
            raise ValueError("approval decision is not approved")
        if request.approval_mode is ApprovalMode.STRONG_HUMAN and not decision.strong_confirmation:
            raise ValueError("approved decision lacks strong confirmation")

        package = {
            "approval_request_id": request.request_id,
            "decision_id": decision.decision_id,
            "route": request.route,
            "action": request.action,
            "subject_id": request.subject_id,
            "risk_level": request.risk_level.value,
            "approval_mode": request.approval_mode.value,
            "decided_by": decision.decided_by,
            "decision_rationale": decision.rationale,
            "single_use_requested": True,
            "bounded_to_exact_route_action_subject": True,
        }
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "lineage_package": package,
                "authority_granted": False,
                "action_performed": False,
            },
            artifacts=("decision-lineage-package",),
        )
