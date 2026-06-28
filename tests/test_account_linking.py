from pathlib import Path

import pytest

from business_agents.agents.customer_account_binding_agent import CustomerAccountBindingAgent
from business_agents.capability_registry import capability_for_identity
from business_agents.customer_accounts import CustomerAccountStore, JobCustomerBindingStore
from business_agents.executors.account_link_executor import AccountLinkExecutor
from business_agents.gateway.customer_account_binding_safety_gate import CustomerAccountBindingSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobRecord, JsonlJobStore


def proposal(customer_id="C-1", binding_id="B-1"):
    return CustomerAccountBindingAgent().propose({
        "customer_id": customer_id,
        "display_name": "Name",
        "primary_contact_reference": "ref-1",
        "binding_id": binding_id,
        "job_id": "J-1",
        "_principal_id": "owner-1",
    })


def setup(tmp_path: Path):
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("J-1", "Old Name", "old-ref", "Work", "test"))
    accounts = CustomerAccountStore(tmp_path / "accounts.jsonl")
    links = JobCustomerBindingStore(tmp_path / "links.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    return AccountLinkExecutor(jobs, accounts, links, receipts), jobs, accounts, links, receipts


def run(executor, intent):
    return executor.execute(intent, authorization_id="a", authorization_fingerprint="f", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_gate_and_link(tmp_path: Path) -> None:
    capability = capability_for_identity("customer-account-binding", "create-and-bind-customer")
    assert capability is not None

    item = proposal()
    assert (item.intent.route, item.intent.action) == (capability.route, capability.action)
    assert CustomerAccountBindingSafetyGate().evaluate(item.intent).passed is True

    executor, jobs, accounts, links, receipts = setup(tmp_path)
    result = run(executor, item.intent)
    receipt = receipts.read_all()[-1]

    assert accounts.get("C-1") is not None
    assert links.get_by_job("J-1").customer_id == "C-1"
    assert jobs.require("J-1").customer_name == "Old Name"
    assert receipt.details["snapshot_preserved"] is True
    assert result.output["binding_id"] == "B-1"
    assert result.receipt_id == receipt.receipt_id


def test_duplicate_job_link_fails(tmp_path: Path) -> None:
    executor, _, _, links, _ = setup(tmp_path)
    run(executor, proposal().intent)
    with pytest.raises(ValueError, match="job already linked"):
        run(executor, proposal("C-2", "B-2").intent)
    assert links.get_by_job("J-1").customer_id == "C-1"
