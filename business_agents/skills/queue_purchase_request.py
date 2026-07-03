"""Queue one immutable prepared purchase artifact for explicit human review."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.approval_requests import ApprovalRequest, ApprovalRequestStore
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.prepared_purchase_artifacts import PreparedPurchaseArtifactStore
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class QueuePurchaseRequestSkill(BaseSkill):
    contract = SkillContract(
        skill_id="queue-purchase-request",
        version="2.0.0",
        domain=SkillDomain.PROCUREMENT,
        effect=SkillEffect.STATE_CHANGING,
        approval_mode=ApprovalMode.HUMAN,
        input_fields=("approval_request_id", "artifact_id", "requested_by"),
        output_fields=("approval_request", "artifact_digest", "order_authority", "court_authority"),
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
        artifact_store: PreparedPurchaseArtifactStore,
        approval_store: ApprovalRequestStore,
    ) -> None:
        self._artifact_store = artifact_store
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

        artifact = self._artifact_store.get(inputs["artifact_id"])
        if artifact is None:
            raise ValueError("prepared purchase artifact not found")

        summary = (
            f"Review artifact {artifact.artifact_id} digest {artifact.payload_digest}: "
            f"{artifact.quantity} x {artifact.item_name} from {artifact.supplier_name} "
            f"for {artifact.landed_cost} {artifact.currency} to "
            f"{artifact.delivery_destination_reference}"
        )
        if artifact.review_flags:
            summary += f"; flags: {', '.join(artifact.review_flags)}"

        request = ApprovalRequest(
            request_id=inputs["approval_request_id"],
            route="procurement.order",
            action="place-bounded-order",
            subject_id=artifact.artifact_id,
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
                "artifact_digest": artifact.payload_digest,
                "order_authority": False,
                "court_authority": False,
            },
            artifacts=("approval-request",),
        )
