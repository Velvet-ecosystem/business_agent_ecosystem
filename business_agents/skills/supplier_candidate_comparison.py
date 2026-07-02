"""Read-only comparison of researched supplier candidates."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.contracts import ApprovalMode
from business_agents.procurement import SupplierCandidateStore
from business_agents.procurement_requirements import ProcurementRequirementStore
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class SupplierCandidateComparisonSkill(BaseSkill):
    contract = SkillContract(
        skill_id="supplier-candidate-comparison",
        version="1.1.0",
        domain=SkillDomain.PROCUREMENT,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=("requirement_id",),
        output_fields=("requirement", "candidate_count", "currencies", "candidates", "purchase_authority"),
        external_action=False,
        receipt_required=False,
        artifact_types=("supplier-comparison",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-immediately",
        retry_behavior="safe-read-retry",
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
        if set(inputs) != {"requirement_id"}:
            raise ValueError("supplier-candidate-comparison requires only requirement_id")
        requirement_id = inputs["requirement_id"]
        if not isinstance(requirement_id, str) or not requirement_id.strip():
            raise ValueError("requirement_id must be a non-empty string")

        requirement = self._requirement_store.get(requirement_id)
        if requirement is None:
            raise ValueError("procurement requirement not found")

        candidates = self._candidate_store.list_for_requirement(requirement_id)
        rows = tuple(
            {
                "candidate_id": candidate.candidate_id,
                "supplier_name": candidate.supplier_name,
                "supplier_part_number": candidate.supplier_part_number,
                "manufacturer_part_number": candidate.manufacturer_part_number,
                "quantity": candidate.quantity,
                "currency": candidate.currency,
                "unit_price": str(candidate.unit_price),
                "shipping_cost": str(candidate.shipping_cost),
                "landed_cost": str(candidate.landed_cost),
                "source_reference": candidate.source_reference,
                "compatibility_evidence": candidate.compatibility_evidence,
                "risk_flags": candidate.risk_flags,
            }
            for candidate in candidates
        )
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "requirement": {
                    "requirement_id": requirement.requirement_id,
                    "item_name": requirement.item_name,
                    "quantity": requirement.quantity,
                    "intended_use": requirement.intended_use,
                    "target_budget": str(requirement.target_budget),
                    "currency": requirement.currency,
                    "urgency": requirement.urgency,
                    "status": requirement.status.value,
                },
                "candidate_count": len(rows),
                "currencies": tuple(sorted({candidate.currency for candidate in candidates})),
                "candidates": rows,
                "purchase_authority": False,
            },
            artifacts=("supplier-comparison",),
        )
