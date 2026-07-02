"""Immutable prepared purchase artifacts with canonical payload digests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class PreparedPurchaseArtifact:
    artifact_id: str
    requirement_id: str
    candidate_id: str
    item_name: str
    intended_use: str
    supplier_name: str
    supplier_part_number: str
    manufacturer_part_number: str
    quantity: int
    currency: str
    unit_price: str
    shipping_cost: str
    landed_cost: str
    target_budget: str
    delivery_destination_reference: str
    source_reference: str
    compatibility_evidence: tuple[str, ...]
    review_flags: tuple[str, ...]
    required_approval: str
    payload_digest: str

    def __post_init__(self) -> None:
        for name in (
            "artifact_id",
            "requirement_id",
            "candidate_id",
            "item_name",
            "intended_use",
            "supplier_name",
            "supplier_part_number",
            "manufacturer_part_number",
            "currency",
            "unit_price",
            "shipping_cost",
            "landed_cost",
            "target_budget",
            "delivery_destination_reference",
            "source_reference",
            "required_approval",
            "payload_digest",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        for name in ("compatibility_evidence", "review_flags"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError(f"{name} must contain non-empty strings")
        expected = self.calculate_payload_digest(self.payload())
        if self.payload_digest != expected:
            raise ValueError("payload_digest does not match canonical payload")

    def payload(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "requirement_id": self.requirement_id,
            "candidate_id": self.candidate_id,
            "item_name": self.item_name,
            "intended_use": self.intended_use,
            "supplier_name": self.supplier_name,
            "supplier_part_number": self.supplier_part_number,
            "manufacturer_part_number": self.manufacturer_part_number,
            "quantity": self.quantity,
            "currency": self.currency,
            "unit_price": self.unit_price,
            "shipping_cost": self.shipping_cost,
            "landed_cost": self.landed_cost,
            "target_budget": self.target_budget,
            "delivery_destination_reference": self.delivery_destination_reference,
            "source_reference": self.source_reference,
            "compatibility_evidence": self.compatibility_evidence,
            "review_flags": self.review_flags,
            "required_approval": self.required_approval,
        }

    @staticmethod
    def calculate_payload_digest(payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            dict(payload), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


class PreparedPurchaseArtifactStore:
    """Locked append-only storage for immutable prepared purchase artifacts."""

    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(
            path, schema="prepared-purchase-artifact", version=1
        )

    def create(self, artifact: PreparedPurchaseArtifact) -> PreparedPurchaseArtifact:
        self._storage.append_unique(asdict(artifact), field="artifact_id")
        return artifact

    def get(self, artifact_id: str) -> PreparedPurchaseArtifact | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("artifact_id") == artifact_id:
                return self._from_payload(payload)
        return None

    @staticmethod
    def _from_payload(payload: dict[str, Any]) -> PreparedPurchaseArtifact:
        return PreparedPurchaseArtifact(
            artifact_id=str(payload["artifact_id"]),
            requirement_id=str(payload["requirement_id"]),
            candidate_id=str(payload["candidate_id"]),
            item_name=str(payload["item_name"]),
            intended_use=str(payload["intended_use"]),
            supplier_name=str(payload["supplier_name"]),
            supplier_part_number=str(payload["supplier_part_number"]),
            manufacturer_part_number=str(payload["manufacturer_part_number"]),
            quantity=int(payload["quantity"]),
            currency=str(payload["currency"]),
            unit_price=str(payload["unit_price"]),
            shipping_cost=str(payload["shipping_cost"]),
            landed_cost=str(payload["landed_cost"]),
            target_budget=str(payload["target_budget"]),
            delivery_destination_reference=str(payload["delivery_destination_reference"]),
            source_reference=str(payload["source_reference"]),
            compatibility_evidence=tuple(payload["compatibility_evidence"]),
            review_flags=tuple(payload["review_flags"]),
            required_approval=str(payload["required_approval"]),
            payload_digest=str(payload["payload_digest"]),
        )
