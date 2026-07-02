"""Queue a prepared purchase package for explicit human review only."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.approval_requests import ApprovalRequest, ApprovalRequestStore
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.procurement import SupplierCandidateStore
from business_agents.procurement_requirements import ProcurementRequirementStore
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult
from business_agents.skills.prepare_purchase_request import PreparePurchaseRequestSkill


class QueuePurchaseRequestSkill(BaseSkill):
    contract = SkillContract(
        skill_id="queue-purchase-request",
        version="1.0.0",
        domain=SkillDomain.PROCUREMENT,
        effect=SkillEffect.STATE_CHANGING,
        approval_mode=ApprovalMode.HUMAN,
        input_fields=("approval_request_id", "requirement_id", "candidate_id", "requested_by"),
        output_fields=("approval_request", "order_authority", "court_authority"),
        capability_route="approval-request",
        capability_action="create-purchase-review",
        external_action=False,
        receipt_required=False,
        artifact_types=("approval-request",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-before-queue-write",
        retry_behavior="manual-on-duplicate",
    )

    def __init__(
        self,
        requirement_store: ProcurementRequirementStore,
        candidate_store: SupplierCandidateStore,
        approval_store: ApprovalRequestStore,
    ) -> None:
        self._prepare = PreparePurchaseRequestSkill(requirement_store, candidate_store)
        self._approval_store = approval_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if set(inputs) != set(self.contract.input_fields):
            raise ValueError("queue-purchase-request requires exact declared inputs")
        for name in self.contract.input_fields:
            value = inputs[name]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        prepared = self._prepare.run(
            {
                "requirement_id": inputs["requirement_id"],
                "candidate_id": inputs["candidate_id"],
            }
        )
        package = prepared.output["purchase_request"]
        flags = prepared.output["review_flags"]
        summary = (
            f"Review purchase of {package['quantity']} x {package['item_name']} "
            f"from {package['supplier_name']} for {package['landed_cost']} {package['currency']}"
        )
        if flags:
            summary += f"; flags: {', '.join(flags)}"

        request = ApprovalRequest(
            request_id=inputs["approval_request_id"],
            route="procurement.order",
            action="place-bounded-order",
            subject_id=inputs["requirement_id"],
            summary=summary,
            requested_by=inputs["requested_by"],
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
        self._approval_store.create(request)
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "approval_request": {
                    "request_id": request.request_id,
                    "route": request.route,
                    "action": request.action,
                    "subject_id": request.subject_id,
                    "summary": request.summary,
                    "risk_level": request.risk_level.value,
                    "approval_mode": request.approval_mode.value,
                    "status": request.status.value,
                },
                "order_authority": False,
                "court_authority": False,
            },
            artifacts=("approval-request",),
        )
