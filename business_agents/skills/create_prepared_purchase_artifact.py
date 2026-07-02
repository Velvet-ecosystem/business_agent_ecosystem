"""Create an immutable prepared purchase artifact for later review."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.contracts import ApprovalMode
from business_agents.prepared_purchase_artifacts import (
    PreparedPurchaseArtifact,
    PreparedPurchaseArtifactStore,
)
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult
from business_agents.skills.prepare_purchase_request import PreparePurchaseRequestSkill


class CreatePreparedPurchaseArtifactSkill(BaseSkill):
    contract = SkillContract(
        skill_id="create-prepared-purchase-artifact",
        version="1.0.0",
        domain=SkillDomain.PROCUREMENT,
        effect=SkillEffect.STATE_CHANGING,
        approval_mode=ApprovalMode.POLICY,
        input_fields=(
            "artifact_id",
            "requirement_id",
            "candidate_id",
            "delivery_destination_reference",
        ),
        output_fields=("artifact", "order_authority"),
        capability_route="prepared-purchase-artifact",
        capability_action="create",
        external_action=False,
        receipt_required=False,
        artifact_types=("prepared-purchase-artifact",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-before-artifact-write",
        retry_behavior="manual-on-duplicate",
    )

    def __init__(
        self,
        prepare_skill: PreparePurchaseRequestSkill,
        artifact_store: PreparedPurchaseArtifactStore,
    ) -> None:
        self._prepare_skill = prepare_skill
        self._artifact_store = artifact_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if set(inputs) != set(self.contract.input_fields):
            raise ValueError("create-prepared-purchase-artifact requires exact declared inputs")
        for name in self.contract.input_fields:
            value = inputs[name]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        prepared = self._prepare_skill.run(
            {
                "requirement_id": inputs["requirement_id"],
                "candidate_id": inputs["candidate_id"],
            }
        )
        request = prepared.output["purchase_request"]
        payload = {
            **request,
            "artifact_id": inputs["artifact_id"],
            "delivery_destination_reference": inputs["delivery_destination_reference"],
            "review_flags": prepared.output["review_flags"],
        }
        digest = PreparedPurchaseArtifact.calculate_payload_digest(payload)
        artifact = PreparedPurchaseArtifact(
            artifact_id=inputs["artifact_id"],
            requirement_id=request["requirement_id"],
            candidate_id=request["candidate_id"],
            item_name=request["item_name"],
            intended_use=request["intended_use"],
            supplier_name=request["supplier_name"],
            supplier_part_number=request["supplier_part_number"],
            manufacturer_part_number=request["manufacturer_part_number"],
            quantity=request["quantity"],
            currency=request["currency"],
            unit_price=request["unit_price"],
            shipping_cost=request["shipping_cost"],
            landed_cost=request["landed_cost"],
            target_budget=request["target_budget"],
            delivery_destination_reference=inputs["delivery_destination_reference"],
            source_reference=request["source_reference"],
            compatibility_evidence=tuple(request["compatibility_evidence"]),
            review_flags=tuple(prepared.output["review_flags"]),
            required_approval=request["required_approval"],
            payload_digest=digest,
        )
        self._artifact_store.create(artifact)
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "artifact": {
                    **artifact.payload(),
                    "payload_digest": artifact.payload_digest,
                },
                "order_authority": False,
            },
            artifacts=("prepared-purchase-artifact",),
        )
