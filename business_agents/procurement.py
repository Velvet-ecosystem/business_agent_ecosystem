"""Local procurement research records without purchasing authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.estimates import money


@dataclass(frozen=True)
class SupplierCandidate:
    candidate_id: str
    requirement_id: str
    supplier_name: str
    supplier_part_number: str
    manufacturer_part_number: str
    quantity: int
    unit_price: Decimal
    shipping_cost: Decimal
    currency: str
    source_reference: str
    compatibility_evidence: tuple[str, ...]
    risk_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "requirement_id",
            "supplier_name",
            "supplier_part_number",
            "manufacturer_part_number",
            "currency",
            "source_reference",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        if money(self.unit_price) < Decimal("0.00") or money(self.shipping_cost) < Decimal("0.00"):
            raise ValueError("prices cannot be negative")
        if not self.compatibility_evidence:
            raise ValueError("compatibility_evidence must not be empty")
        for name, values in (
            ("compatibility_evidence", self.compatibility_evidence),
            ("risk_flags", self.risk_flags),
        ):
            if not isinstance(values, tuple) or any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{name} must contain non-empty strings")

    @property
    def landed_cost(self) -> Decimal:
        return money(money(self.unit_price) * self.quantity + money(self.shipping_cost))


class SupplierCandidateStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="supplier-candidate")

    def create(self, candidate: SupplierCandidate) -> SupplierCandidate:
        payload = asdict(candidate)
        payload["unit_price"] = str(money(candidate.unit_price))
        payload["shipping_cost"] = str(money(candidate.shipping_cost))
        payload["compatibility_evidence"] = list(candidate.compatibility_evidence)
        payload["risk_flags"] = list(candidate.risk_flags)
        self._storage.append_unique(payload, field="candidate_id")
        return candidate

    def list_for_requirement(self, requirement_id: str) -> tuple[SupplierCandidate, ...]:
        if not isinstance(requirement_id, str) or not requirement_id.strip():
            raise ValueError("requirement_id must be a non-empty string")
        candidates = (
            self._from_payload(payload)
            for payload in self._storage.read_all()
            if payload.get("requirement_id") == requirement_id
        )
        return tuple(sorted(candidates, key=lambda item: item.candidate_id))

    @staticmethod
    def _from_payload(payload: dict) -> SupplierCandidate:
        return SupplierCandidate(
            candidate_id=str(payload["candidate_id"]),
            requirement_id=str(payload["requirement_id"]),
            supplier_name=str(payload["supplier_name"]),
            supplier_part_number=str(payload["supplier_part_number"]),
            manufacturer_part_number=str(payload["manufacturer_part_number"]),
            quantity=int(payload["quantity"]),
            unit_price=money(payload["unit_price"]),
            shipping_cost=money(payload["shipping_cost"]),
            currency=str(payload["currency"]),
            source_reference=str(payload["source_reference"]),
            compatibility_evidence=tuple(str(item) for item in payload["compatibility_evidence"]),
            risk_flags=tuple(str(item) for item in payload.get("risk_flags", [])),
        )
