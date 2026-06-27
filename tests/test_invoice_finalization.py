from pathlib import Path

import pytest

from business_agents.agents.invoice_finalization_agent import InvoiceFinalizationAgent
from business_agents.executors.invoice_finalization_executor import InvoiceFinalizationExecutor
from business_agents.gateway.invoice_finalization_safety_gate import InvoiceFinalizationSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.invoice_drafts import InvoiceDraft
from business_agents.invoice_finalizations import InvoiceFinalizationStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from decimal import Decimal


def job() -> JobRecord:
    return JobRecord("JOB-1", "Alex Morgan", "alex@example.com", "Install system", "test", JobStatus.COMPLETED)


def context() -> dict[str, str]:
    return {"finalization_id": "FIN-1", "invoice_id": "INV-1", "job_id": "JOB-1", "_principal_id": "owner-1"}


def execute(executor: InvoiceFinalizationExecutor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_uses_verified_principal_and_gate_passes() -> None:
    proposal = InvoiceFinalizationAgent().propose(context())
    assert proposal.intent.parameters["approved_by"] == "owner-1"
    assert InvoiceFinalizationSafetyGate().evaluate(proposal.intent).passed is True


def test_executor_rejects_missing_draft(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(job())
    executor = InvoiceFinalizationExecutor(jobs, JsonlInvoiceDraftStore(tmp_path / "invoices.jsonl"), InvoiceFinalizationStore(tmp_path / "finalizations.jsonl"), JsonlReceiptStore(tmp_path / "receipts.jsonl"))
    with pytest.raises(ValueError, match="invoice draft not found"):
        execute(executor, InvoiceFinalizationAgent().propose(context()).intent)


def test_executor_rejects_draft_for_other_job(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(job())
    invoices = JsonlInvoiceDraftStore(tmp_path / "invoices.jsonl")
    invoices.create(InvoiceDraft("INV-1", "JOB-2", "EVID-2", "CAD", Decimal("100.00"), Decimal("5.00"), Decimal("105.00")))
    executor = InvoiceFinalizationExecutor(jobs, invoices, InvoiceFinalizationStore(tmp_path / "finalizations.jsonl"), JsonlReceiptStore(tmp_path / "receipts.jsonl"))
    with pytest.raises(ValueError, match="different job"):
        execute(executor, InvoiceFinalizationAgent().propose(context()).intent)


def test_finalization_is_durable_and_receipted(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(job())
    invoices = JsonlInvoiceDraftStore(tmp_path / "invoices.jsonl")
    invoices.create(InvoiceDraft("INV-1", "JOB-1", "EVID-1", "CAD", Decimal("100.00"), Decimal("5.00"), Decimal("105.00")))
    finalizations = InvoiceFinalizationStore(tmp_path / "finalizations.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    result = execute(InvoiceFinalizationExecutor(jobs, invoices, finalizations, receipts), InvoiceFinalizationAgent().propose(context()).intent)
    assert finalizations.get("FIN-1") is not None
    assert result.output["invoice_id"] == "INV-1"
    assert receipts.read_all()[-1].details["approved_by"] == "owner-1"
