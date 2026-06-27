"""Durable estimate drafts with deterministic decimal arithmetic."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping

from business_agents.compatible_storage import CompatibleLockedJsonlFile

_CENT = Decimal("0.01")


def money(value: str | int | float | Decimal) -> Decimal:
    """Normalize a monetary value to two decimal places."""
    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise ValueError("invalid monetary value") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("monetary values must be finite and non-negative")
    return amount.quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class EstimateDraft:
    estimate_id: str
    job_id: str
    currency: str
    labour_subtotal: Decimal
    materials_subtotal: Decimal
    contingency_amount: Decimal
    margin_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    notes: str = ""
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name, value in (("estimate_id", self.estimate_id), ("job_id", self.job_id), ("currency", self.currency)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.currency.strip()) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        for field_name in (
            "labour_subtotal", "materials_subtotal", "contingency_amount",
            "margin_amount", "tax_amount", "total",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, Decimal) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative Decimal")
        expected = money(
            self.labour_subtotal + self.materials_subtotal + self.contingency_amount
            + self.margin_amount + self.tax_amount
        )
        if self.total != expected:
            raise ValueError("estimate total does not match components")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")


class JsonlEstimateStore:
    """Locked append-only estimate store with legacy compatibility."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(path, schema="estimate-draft")

    def create(self, draft: EstimateDraft) -> EstimateDraft:
        payload = asdict(draft)
        for key in (
            "labour_subtotal", "materials_subtotal", "contingency_amount",
            "margin_amount", "tax_amount", "total",
        ):
            payload[key] = str(payload[key])
        payload["metadata"] = None if draft.metadata is None else dict(draft.metadata)
        try:
            self._storage.append_unique(payload, field="estimate_id")
        except ValueError as exc:
            if str(exc).startswith("record already exists for estimate_id:"):
                raise ValueError(f"estimate already exists: {draft.estimate_id}") from exc
            raise
        return draft

    def get(self, estimate_id: str) -> EstimateDraft | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("estimate_id") == estimate_id:
                metadata = payload.get("metadata")
                return EstimateDraft(
                    estimate_id=str(payload["estimate_id"]),
                    job_id=str(payload["job_id"]),
                    currency=str(payload["currency"]),
                    labour_subtotal=money(payload["labour_subtotal"]),
                    materials_subtotal=money(payload["materials_subtotal"]),
                    contingency_amount=money(payload["contingency_amount"]),
                    margin_amount=money(payload["margin_amount"]),
                    tax_amount=money(payload["tax_amount"]),
                    total=money(payload["total"]),
                    notes=str(payload.get("notes", "")),
                    metadata=None if metadata is None else dict(metadata),
                )
        return None
