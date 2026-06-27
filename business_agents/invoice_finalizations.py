"""Durable records proving a reviewed invoice draft was finalized."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class InvoiceFinalization:
    finalization_id: str
    invoice_id: str
    job_id: str
    approved_by: str

    def __post_init__(self) -> None:
        for name in ("finalization_id", "invoice_id", "job_id", "approved_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class InvoiceFinalizationStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="invoice-finalization")

    def create(self, record: InvoiceFinalization) -> InvoiceFinalization:
        self._storage.append_unique(asdict(record), field="finalization_id")
        return record

    def get(self, finalization_id: str) -> InvoiceFinalization | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("finalization_id") == finalization_id:
                return InvoiceFinalization(**payload)
        return None
