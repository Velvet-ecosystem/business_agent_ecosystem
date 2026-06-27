"""Durable confirmations for an explicitly authorized invoice handoff."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class InvoiceHandoffConfirmation:
    confirmation_id: str
    preparation_id: str
    invoice_id: str
    job_id: str
    channel_reference: str
    recipient_reference: str
    confirmed_by: str

    def __post_init__(self) -> None:
        for name in ("confirmation_id", "preparation_id", "invoice_id", "job_id", "channel_reference", "recipient_reference", "confirmed_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class InvoiceHandoffConfirmationStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="invoice-handoff-confirmation")

    def create(self, record: InvoiceHandoffConfirmation) -> InvoiceHandoffConfirmation:
        self._storage.append_unique(asdict(record), field="confirmation_id")
        return record

    def get(self, confirmation_id: str) -> InvoiceHandoffConfirmation | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("confirmation_id") == confirmation_id:
                return InvoiceHandoffConfirmation(**payload)
        return None
