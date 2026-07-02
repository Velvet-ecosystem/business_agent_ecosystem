"""Durable procurement requirements that precede supplier research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.estimates import money


class ProcurementRequirementStatus(str, Enum):
    RESEARCH = "research"
    READY_FOR_REVIEW = "ready-for-review"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ProcurementRequirement:
    requirement_id: str
    item_name: str
    quantity: int
    intended_use: str
    compatibility_constraints: tuple[str, ...]
    acceptable_substitutions: tuple[str, ...]
    target_budget: Decimal
    currency: str
    required_evidence: tuple[str, ...]
    urgency: str
    source_reference: str
    status: ProcurementRequirementStatus = ProcurementRequirementStatus.RESEARCH

    def __post_init__(self) -> None:
        for name in ("requirement_id", "item_name", "intended_use", "currency", "urgency", "source_reference"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        if not isinstance(self.target_budget, Decimal) or self.target_budget < 0:
            raise ValueError("target_budget must be a non-negative Decimal")
        for name, values in (
            ("compatibility_constraints", self.compatibility_constraints),
            ("acceptable_substitutions", self.acceptable_substitutions),
            ("required_evidence", self.required_evidence),
        ):
            if not isinstance(values, tuple) or any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{name} must contain non-empty strings")
        if not self.compatibility_constraints or not self.required_evidence:
            raise ValueError("constraints and required evidence must not be empty")
        if not isinstance(self.status, ProcurementRequirementStatus):
            raise ValueError("status must be a ProcurementRequirementStatus")


class ProcurementRequirementStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="procurement-requirement")

    def create(self, requirement: ProcurementRequirement) -> ProcurementRequirement:
        payload = asdict(requirement)
        payload["target_budget"] = str(money(requirement.target_budget))
        payload["status"] = requirement.status.value
        for key in ("compatibility_constraints", "acceptable_substitutions", "required_evidence"):
            payload[key] = list(payload[key])
        self._storage.append_unique(payload, field="requirement_id")
        return requirement

    def get(self, requirement_id: str) -> ProcurementRequirement | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("requirement_id") == requirement_id:
                return ProcurementRequirement(
                    requirement_id=str(payload["requirement_id"]),
                    item_name=str(payload["item_name"]),
                    quantity=int(payload["quantity"]),
                    intended_use=str(payload["intended_use"]),
                    compatibility_constraints=tuple(str(item) for item in payload["compatibility_constraints"]),
                    acceptable_substitutions=tuple(str(item) for item in payload.get("acceptable_substitutions", [])),
                    target_budget=money(payload["target_budget"]),
                    currency=str(payload["currency"]),
                    required_evidence=tuple(str(item) for item in payload["required_evidence"]),
                    urgency=str(payload["urgency"]),
                    source_reference=str(payload["source_reference"]),
                    status=ProcurementRequirementStatus(str(payload["status"])),
                )
        return None
