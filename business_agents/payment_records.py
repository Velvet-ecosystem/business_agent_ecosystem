"""Durable records for reported payments and invoice reconciliation."""

from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.estimates import money


@dataclass(frozen=True)
class PaymentRecord:
    payment_id: str
    invoice_id: str
    job_id: str
    handoff_confirmation_id: str
    amount: Decimal
    currency: str
    source_reference: str
    recorded_by: str

    def __post_init__(self) -> None:
        for name in ("payment_id", "invoice_id", "job_id", "handoff_confirmation_id", "currency", "source_reference", "recorded_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        if not isinstance(self.amount, Decimal) or self.amount <= 0:
            raise ValueError("amount must be a positive Decimal")


class PaymentRecordStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="payment-record")

    def create(self, record: PaymentRecord) -> PaymentRecord:
        payload = asdict(record)
        payload["amount"] = str(record.amount)
        self._storage.append_unique(payload, field="payment_id")
        return record

    def get(self, payment_id: str) -> PaymentRecord | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("payment_id") == payment_id:
                return self._from_payload(payload)
        return None

    def list_for_invoice(self, invoice_id: str) -> tuple[PaymentRecord, ...]:
        return tuple(self._from_payload(payload) for payload in self._storage.read_all() if payload.get("invoice_id") == invoice_id)

    def total_for_invoice(self, invoice_id: str) -> Decimal:
        total = sum((record.amount for record in self.list_for_invoice(invoice_id)), Decimal("0"))
        return money(total)

    @staticmethod
    def _from_payload(payload) -> PaymentRecord:
        return PaymentRecord(
            payment_id=str(payload["payment_id"]),
            invoice_id=str(payload["invoice_id"]),
            job_id=str(payload["job_id"]),
            handoff_confirmation_id=str(payload["handoff_confirmation_id"]),
            amount=money(payload["amount"]),
            currency=str(payload["currency"]),
            source_reference=str(payload["source_reference"]),
            recorded_by=str(payload["recorded_by"]),
        )
