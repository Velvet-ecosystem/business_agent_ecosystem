from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.invoice_drafts import InvoiceDraft
from business_agents.skills.invoice_draft_summary import InvoiceDraftSummarySkill


def _draft(invoice_id: str, job_id: str, total: str) -> InvoiceDraft:
    amount = Decimal(total)
    return InvoiceDraft(
        invoice_id=invoice_id,
        job_id=job_id,
        evidence_id=f"evidence-{job_id}",
        currency="CAD",
        subtotal=amount,
        tax_amount=Decimal("0.00"),
        total=amount,
        notes="private note",
    )


def test_invoice_draft_summary_is_read_only_and_draft_scoped(tmp_path: Path) -> None:
    path = tmp_path / "invoice_drafts.jsonl"
    store = JsonlInvoiceDraftStore(path)
    store.create(_draft("inv-002", "job-002", "20.00"))
    store.create(_draft("inv-001", "job-001", "10.00"))

    before = path.read_text(encoding="utf-8")
    result = InvoiceDraftSummarySkill(store).run({})
    after = path.read_text(encoding="utf-8")

    assert result.output == {
        "scope": "invoice-drafts-only",
        "draft_count": 2,
        "drafts": (
            {"invoice_id": "inv-001", "job_id": "job-001", "currency": "CAD", "total": "10.00"},
            {"invoice_id": "inv-002", "job_id": "job-002", "currency": "CAD", "total": "20.00"},
        ),
    }
    assert before == after
    rendered = repr(result.output)
    assert "private note" not in rendered
    assert "paid" not in rendered
    assert "overdue" not in rendered
    assert "outstanding" not in rendered


def test_invoice_draft_summary_rejects_inputs(tmp_path: Path) -> None:
    skill = InvoiceDraftSummarySkill(JsonlInvoiceDraftStore(tmp_path / "invoice_drafts.jsonl"))

    with pytest.raises(ValueError, match="accepts no inputs"):
        skill.run({"status": "unpaid"})
