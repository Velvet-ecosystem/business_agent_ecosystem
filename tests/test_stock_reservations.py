from pathlib import Path

import pytest

from business_agents.agents.stock_reservation_agent import StockReservationAgent
from business_agents.capability_registry import capability_for_identity
from business_agents.executors.stock_reservation_executor import StockReservationExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.stock_reservation_safety_gate import StockReservationSafetyGate
from business_agents.jobs import JobRecord, JsonlJobStore
from business_agents.stock_reservations import StockReservationStore


def context(reservation_id="RES-1"):
    return {
        "reservation_id": reservation_id,
        "job_id": "JOB-1",
        "item_reference": "ITEM-1",
        "quantity_reference": "QTY-2",
        "location_reference": "BIN-A",
        "_principal_id": "owner-1",
    }


def build(tmp_path: Path):
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    jobs.create(JobRecord("JOB-1", "Name", "contact", "Work", "test"))
    reservations = StockReservationStore(tmp_path / "reservations.jsonl")
    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    return StockReservationExecutor(jobs, reservations, receipts), reservations, receipts


def run(executor, intent):
    return executor.execute(intent, authorization_id="auth-1", authorization_fingerprint="fp-1", authorization_issued_at=1.0, authorization_expires_at=2.0)


def test_agent_gate_and_record(tmp_path: Path) -> None:
    capability = capability_for_identity("stock-reservation", "record-stock-reservation")
    assert capability is not None

    proposal = StockReservationAgent().propose(context())
    assert (proposal.intent.route, proposal.intent.action) == (capability.route, capability.action)
    assert StockReservationSafetyGate().evaluate(proposal.intent).passed is True

    executor, reservations, receipts = build(tmp_path)
    result = run(executor, proposal.intent)
    receipt = receipts.read_all()[-1]

    assert reservations.get("RES-1").job_id == "JOB-1"
    assert receipt.details["stock_changed"] is False
    assert result.output["stock_changed"] is False
    assert result.receipt_id == receipt.receipt_id


def test_duplicate_reservation_id_fails(tmp_path: Path) -> None:
    executor, reservations, _ = build(tmp_path)
    run(executor, StockReservationAgent().propose(context()).intent)
    with pytest.raises(ValueError):
        run(executor, StockReservationAgent().propose(context()).intent)
    assert reservations.get("RES-1") is not None
