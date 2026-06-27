from pathlib import Path

import pytest

from business_agents.agents.invoice_draft_agent import InvoiceDraftAgent
from business_agents.completion_evidence import CompletionEvidence, CompletionEvidenceStore
from business_agents.executors.invoice_draft_executor import InvoiceDraftExecutor
from business_agents.gateway.invoice_draft_safety_gate import InvoiceDraftSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def completed_job() -> JobRecord:
    return JobRecord("JOB-1", "Alex Morgan", "alex@example.com", "Install system", "test", JobStatus.COMPLETED)


def context() -> dict[str, object]:
    return {
        "invoice_id": "INV-1",
        "job_id": "JOB-1",
        "job_status": "completed",
        "evidence_id": "EVID-1",
        "currency": "CAD",
        "subtotal": "100.00",
        "tax_rate": "0.05",
        "notes": "Local draft only",
    }


def execute(executor: InvoiceDraftExecutor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_calculates_deterministic_draft_total() -> None:
    proposal = InvoiceDraftAgent().propose(context())
    assert proposal.intent.parameters["tax_amount"] == "5.00"
    assert proposal.intent.parameters["total"] == "105.00"
    assert InvoiceDraftSafetyGate().evaluate(proposal.intent).passed is True


def test_gate_rejects_unexpected_fields() -> None:
    proposal = InvoiceDraftAgent().propose(context())
    params = dict(proposal.intent.parameters)
    params["unexpected"] = True
    from business_agents.contracts import BusinessIntent
    altered = BusinessIntent(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters=params,
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )
    assert InvoiceDraftSafetyGate().evaluate(altered).passed is False


def test_executor_requires_matching_completion_evidence(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    evidence = CompletionEvidenceStore(tmp_path / "evidence.jsonl")
    invoices = JsonlInvoiceDraftStore(tmp_path / "invoices.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs.create(completed_job())
    evidence.create(CompletionEvidence("EVID-1", "JOB-2", "owner-1", "Done", ("Checked",)))
    executor = InvoiceDraftExecutor(jobs, evidence, invoices, receipts)
    with pytest.raises(ValueError, match="different job"):
        execute(executor, InvoiceDraftAgent().propose(context()).intent)
    assert invoices.get("INV-1") is None


def test_approved_invoice_draft_is_durable_and_receipted(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    evidence = CompletionEvidenceStore(tmp_path / "evidence.jsonl")
    invoices = JsonlInvoiceDraftStore(tmp_path / "invoices.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    jobs.create(completed_job())
    evidence.create(CompletionEvidence("EVID-1", "JOB-1", "owner-1", "Done", ("Checked",)))
    result = execute(InvoiceDraftExecutor(jobs, evidence, invoices, receipts), InvoiceDraftAgent().propose(context()).intent)
    assert result.output["draft_only"] is True
    assert result.output["total"] == "105.00"
    assert invoices.get("INV-1") is not None
    assert receipts.read_all()[-1].details["draft_only"] is True
