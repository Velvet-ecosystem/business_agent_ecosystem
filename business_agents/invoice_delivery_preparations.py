"""Durable local preparation records for finalized invoices."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class InvoiceDeliveryPreparation:
    preparation_id: str
    finalization_id: str
    invoice_id: str
    job_id: str
    prepared_by: str

    def __post_init__(self) -> None:
        for name in ("preparation_id", "finalization_id", "invoice_id", "job_id", "prepared_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class InvoiceDeliveryPreparationStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="invoice-delivery-preparation")

    def create(self, record: InvoiceDeliveryPreparation) -> InvoiceDeliveryPreparation:
        self._storage.append_unique(asdict(record), field="preparation_id")
        return record

    def get(self, preparation_id: str) -> InvoiceDeliveryPreparation | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("preparation_id") == preparation_id:
                return InvoiceDeliveryPreparation(**payload)
        return None
