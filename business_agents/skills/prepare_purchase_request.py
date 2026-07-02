"""Preparation-only purchase request assembled from stored procurement records."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.contracts import ApprovalMode
from business_agents.procurement import SupplierCandidateStore
from business_agents.procurement_requirements import (
    ProcurementRequirementStatus,
    ProcurementRequirementStore,
)
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class PreparePurchaseRequestSkill(BaseSkill):
    """Prepare exact commercial terms for review without ordering anything."""

    contract = SkillContract(
        skill_id="prepare-purchase-request",
        version="1.0.0",
        domain=SkillDomain.PROCUREMENT,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=("requirement_id", "candidate_id"),
        output_fields=("purchase_request", "review_flags", "order_authority"),
        external_action=False,
        receipt_required=False,
        artifact_types=("prepared-purchase-request",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-before-approval-request",
        retry_behavior="safe-preparation-retry",
    )

    def __init__(
        self,
        requirement_store: ProcurementRequirementStore,
        candidate_store: SupplierCandidateStore,
    ) -> None:
        self._requirement_store = requirement_store
        self._candidate_store = candidate_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if set(inputs) != {"requirement_id", "candidate_id"}:
            raise ValueError("prepare-purchase-request requires exact declared inputs")

        requirement_id = inputs["requirement_id"]
        candidate_id = inputs["candidate_id"]
        for name, value in (("requirement_id", requirement_id), ("candidate_id", candidate_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        requirement = self._requirement_store.get(requirement_id)
        if requirement is None:
            raise ValueError("procurement requirement not found")
        if requirement.status in {
            ProcurementRequirementStatus.FULFILLED,
            ProcurementRequirementStatus.CANCELLED,
        }:
            raise ValueError("procurement requirement is not open for preparation")

        candidate = next(
            (
                item
                for item in self._candidate_store.list_for_requirement(requirement_id)
                if item.candidate_id == candidate_id
            ),
            None,
        )
        if candidate is None:
            raise ValueError("supplier candidate not found for requirement")

        flags: list[str] = list(candidate.risk_flags)
        if candidate.currency != requirement.currency:
            flags.append("currency-mismatch")
        if candidate.quantity != requirement.quantity:
            flags.append("quantity-mismatch")
        if candidate.currency == requirement.currency and candidate.landed_cost > requirement.target_budget:
            flags.append("over-target-budget")

        request = {
            "requirement_id": requirement.requirement_id,
            "candidate_id": candidate.candidate_id,
            "item_name": requirement.item_name,
            "intended_use": requirement.intended_use,
            "supplier_name": candidate.supplier_name,
            "supplier_part_number": candidate.supplier_part_number,
            "manufacturer_part_number": candidate.manufacturer_part_number,
            "quantity": candidate.quantity,
            "currency": candidate.currency,
            "unit_price": str(candidate.unit_price),
            "shipping_cost": str(candidate.shipping_cost),
            "landed_cost": str(candidate.landed_cost),
            "target_budget": str(requirement.target_budget),
            "source_reference": candidate.source_reference,
            "compatibility_evidence": candidate.compatibility_evidence,
            "required_approval": ApprovalMode.STRONG_HUMAN.value,
        }
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "purchase_request": request,
                "review_flags": tuple(dict.fromkeys(flags)),
                "order_authority": False,
            },
            artifacts=("prepared-purchase-request",),
        )
