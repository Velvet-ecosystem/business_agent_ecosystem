"""Local draft-only invoice records. No sending or payment behavior."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class InvoiceDraft:
    invoice_id: str
    job_id: str
    evidence_id: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("invoice_id", "job_id", "evidence_id", "currency"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        if any(not isinstance(value, Decimal) or value < 0 for value in (self.subtotal, self.tax_amount, self.total)):
            raise ValueError("invoice amounts must be non-negative Decimal values")
        if self.total != self.subtotal + self.tax_amount:
            raise ValueError("invoice total does not match components")
