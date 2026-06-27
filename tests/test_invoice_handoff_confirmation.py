from pathlib import Path

import pytest

from business_agents.agents.invoice_handoff_confirmation_agent import InvoiceHandoffConfirmationAgent
from business_agents.executors.invoice_handoff_confirmation_executor import InvoiceHandoffConfirmationExecutor
from business_agents.gateway.invoice_handoff_confirmation_safety_gate import InvoiceHandoffConfirmationSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_delivery_preparations import InvoiceDeliveryPreparation, InvoiceDeliveryPreparationStore
from business_agents.invoice_handoff_confirmations import InvoiceHandoffConfirmationStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def completed_job() -> JobRecord:
    return JobRecord("JOB-1", "A", "a@b.c", "Work", "test", JobStatus.COMPLETED)


def context() -> dict[str, str]:
    return {
        "confirmation_id": "CONF-1",
        "preparation_id": "PREP-1",
        "invoice_id": "INV-1",
        "job_id": "JOB-1",
        "channel_reference": "email-record-1",
        "recipient_reference": "customer-ref-1",
        "_principal_id": "owner-1",
    }


def execute(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_and_gate() -> None:
    proposal = InvoiceHandoffConfirmationAgent().propose(context())
    assert proposal.intent.parameters["confirmed_by"] == "owner-1"
    assert InvoiceHandoffConfirmationSafetyGate().evaluate(proposal.intent).passed is True


def test_missing_preparation_fails_closed(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(completed_job())
    executor = InvoiceHandoffConfirmationExecutor(jobs, InvoiceDeliveryPreparationStore(tmp_path / "preparations.jsonl"), InvoiceHandoffConfirmationStore(tmp_path / "confirmations.jsonl"), JsonlReceiptStore(tmp_path / "receipts.jsonl"))
    with pytest.raises(ValueError, match="invoice preparation not found"):
        execute(executor, InvoiceHandoffConfirmationAgent().propose(context()).intent)


def test_confirmation_is_durable_and_receipted(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(completed_job())
    preparations = InvoiceDeliveryPreparationStore(tmp_path / "preparations.jsonl")
    preparations.create(InvoiceDeliveryPreparation("PREP-1", "FIN-1", "INV-1", "JOB-1", "owner-1"))
    confirmations = InvoiceHandoffConfirmationStore(tmp_path / "confirmations.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    result = execute(InvoiceHandoffConfirmationExecutor(jobs, preparations, confirmations, receipts), InvoiceHandoffConfirmationAgent().propose(context()).intent)
    assert confirmations.get("CONF-1") is not None
    assert result.output["invoice_id"] == "INV-1"
    assert receipts.read_all()[-1].details["confirmed_by"] == "owner-1"
