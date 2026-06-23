"""Durable estimate drafts with deterministic decimal arithmetic."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping

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
            "labour_subtotal",
            "materials_subtotal",
            "contingency_amount",
            "margin_amount",
            "tax_amount",
            "total",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, Decimal) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative Decimal")
        expected = money(
            self.labour_subtotal
            + self.materials_subtotal
            + self.contingency_amount
            + self.margin_amount
            + self.tax_amount
        )
        if self.total != expected:
            raise ValueError("estimate total does not match components")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")


class JsonlEstimateStore:
    """Append-only store for internal estimate drafts."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, draft: EstimateDraft) -> EstimateDraft:
        if self.get(draft.estimate_id) is not None:
            raise ValueError(f"estimate already exists: {draft.estimate_id}")
        payload = asdict(draft)
        for key in (
            "labour_subtotal",
            "materials_subtotal",
            "contingency_amount",
            "margin_amount",
            "tax_amount",
            "total",
        ):
            payload[key] = str(payload[key])
        payload["metadata"] = dict(draft.metadata or {})
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        return draft

    def get(self, estimate_id: str) -> EstimateDraft | None:
        if not self.path.exists():
            return None
        found: EstimateDraft | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid estimate event at line {line_number}") from exc
                if payload.get("estimate_id") == estimate_id:
                    found = EstimateDraft(
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
                        metadata=dict(payload.get("metadata", {})),
                    )
        return found
