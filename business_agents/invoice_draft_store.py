"""Locked append-only storage for local invoice drafts."""

from dataclasses import asdict
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.estimates import money
from business_agents.invoice_drafts import InvoiceDraft


class JsonlInvoiceDraftStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="invoice-draft")

    def create(self, draft: InvoiceDraft) -> InvoiceDraft:
        payload = asdict(draft)
        for key in ("subtotal", "tax_amount", "total"):
            payload[key] = str(payload[key])
        try:
            self._storage.append_unique(payload, field="invoice_id")
        except ValueError as exc:
            if str(exc).startswith("record already exists for invoice_id:"):
                raise ValueError(f"invoice already exists: {draft.invoice_id}") from exc
            raise
        return draft

    def get(self, invoice_id: str) -> InvoiceDraft | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("invoice_id") == invoice_id:
                return InvoiceDraft(
                    invoice_id=str(payload["invoice_id"]),
                    job_id=str(payload["job_id"]),
                    evidence_id=str(payload["evidence_id"]),
                    currency=str(payload["currency"]),
                    subtotal=money(payload["subtotal"]),
                    tax_amount=money(payload["tax_amount"]),
                    total=money(payload["total"]),
                    notes=str(payload.get("notes", "")),
                )
        return None
