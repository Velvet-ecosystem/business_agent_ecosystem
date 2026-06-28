from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.agents.payment_recording_agent import PaymentRecordingAgent
from business_agents.executors.reported_amount_recording_executor import ReportedAmountRecordingExecutor
from business_agents.gateway.payment_recording_safety_gate import PaymentRecordingSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.invoice_drafts import InvoiceDraft
from business_agents.invoice_handoff_confirmations import InvoiceHandoffConfirmation, InvoiceHandoffConfirmationStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.payment_records import PaymentRecordStore


def make_context(record_id: str = "REC-1", amount: str = "40.00") -> dict[str, str]:
    return {
        "payment_id": record_id,
        "invoice_id": "INV-1",
        "job_id": "JOB-1",
        "handoff_confirmation_id": "CONF-1",
        "amount": amount,
        "currency": "CAD",
        "source_reference": "source-1",
        "_principal_id": "owner-1",
    }


def build_executor(tmp_path: Path):
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("JOB-1", "A", "a@b.c", "Work", "test", JobStatus.COMPLETED))
    invoices = JsonlInvoiceDraftStore(tmp_path / "invoices.jsonl")
    invoices.create(InvoiceDraft("INV-1", "JOB-1", "EVID-1", "CAD", Decimal("100.00"), Decimal("5.00"), Decimal("105.00")))
    handoffs = InvoiceHandoffConfirmationStore(tmp_path / "handoffs.jsonl")
    handoffs.create(InvoiceHandoffConfirmation("CONF-1", "PREP-1", "INV-1", "JOB-1", "channel-1", "recipient-1", "owner-1"))
    records = PaymentRecordStore(tmp_path / "records.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    return ReportedAmountRecordingExecutor(jobs, invoices, handoffs, records, receipts), records, receipts


def run(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_and_gate() -> None:
    proposal = PaymentRecordingAgent().propose(make_context())
    assert proposal.intent.parameters["recorded_by"] == "owner-1"
    assert PaymentRecordingSafetyGate().evaluate(proposal.intent).passed is True


def test_partial_then_complete(tmp_path: Path) -> None:
    executor, records, receipts = build_executor(tmp_path)
    first = run(executor, PaymentRecordingAgent().propose(make_context()).intent)
    second = run(executor, PaymentRecordingAgent().propose(make_context("REC-2", "65.00")).intent)
    receipt = receipts.read_all()[-1]
    assert first.output["state"] == "partial"
    assert second.output["state"] == "complete"
    assert records.total_for_invoice("INV-1") == Decimal("105.00")
    assert second.receipt_id == receipt.receipt_id
    assert receipt.details["remaining"] == "0.00"


def test_excess_fails_closed(tmp_path: Path) -> None:
    executor, records, _ = build_executor(tmp_path)
    run(executor, PaymentRecordingAgent().propose(make_context()).intent)
    with pytest.raises(ValueError, match="recorded total exceeds target total"):
        run(executor, PaymentRecordingAgent().propose(make_context("REC-2", "66.00")).intent)
    assert records.total_for_invoice("INV-1") == Decimal("40.00")
