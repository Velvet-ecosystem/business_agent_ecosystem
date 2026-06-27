from pathlib import Path

import pytest

from business_agents.agents.invoice_delivery_preparation_agent import InvoiceDeliveryPreparationAgent
from business_agents.executors.invoice_delivery_preparation_executor import InvoiceDeliveryPreparationExecutor
from business_agents.gateway.invoice_delivery_preparation_safety_gate import InvoiceDeliveryPreparationSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.invoice_delivery_preparations import InvoiceDeliveryPreparationStore
from business_agents.invoice_finalizations import InvoiceFinalization, InvoiceFinalizationStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore


def completed_job() -> JobRecord:
    return JobRecord("JOB-1", "A", "a@b.c", "Work", "test", JobStatus.COMPLETED)


def context() -> dict[str, str]:
    return {"preparation_id": "PREP-1", "finalization_id": "FIN-1", "invoice_id": "INV-1", "job_id": "JOB-1", "_principal_id": "owner-1"}


def execute(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_and_gate() -> None:
    proposal = InvoiceDeliveryPreparationAgent().propose(context())
    assert proposal.intent.parameters["prepared_by"] == "owner-1"
    assert InvoiceDeliveryPreparationSafetyGate().evaluate(proposal.intent).passed is True


def test_missing_finalization_fails_closed(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(completed_job())
    executor = InvoiceDeliveryPreparationExecutor(jobs, InvoiceFinalizationStore(tmp_path / "finalizations.jsonl"), InvoiceDeliveryPreparationStore(tmp_path / "preparations.jsonl"), JsonlReceiptStore(tmp_path / "receipts.jsonl"))
    with pytest.raises(ValueError, match="invoice finalization not found"):
        execute(executor, InvoiceDeliveryPreparationAgent().propose(context()).intent)


def test_preparation_is_durable_and_receipted(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(completed_job())
    finalizations = InvoiceFinalizationStore(tmp_path / "finalizations.jsonl")
    finalizations.create(InvoiceFinalization("FIN-1", "INV-1", "JOB-1", "owner-1"))
    preparations = InvoiceDeliveryPreparationStore(tmp_path / "preparations.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    result = execute(InvoiceDeliveryPreparationExecutor(jobs, finalizations, preparations, receipts), InvoiceDeliveryPreparationAgent().propose(context()).intent)
    assert preparations.get("PREP-1") is not None
    assert result.output["invoice_id"] == "INV-1"
    assert receipts.read_all()[-1].details["prepared_by"] == "owner-1"
