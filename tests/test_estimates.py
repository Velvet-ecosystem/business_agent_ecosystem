"""Tests for draft-only estimate calculation and execution."""

from decimal import Decimal
from pathlib import Path

import pytest

from business_agents.agents.estimate_agent import EstimateAgent
from business_agents.contracts import BusinessIntent
from business_agents.estimates import EstimateDraft, JsonlEstimateStore, money
from business_agents.executors.estimate_executor import EstimateExecutor
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.coordinator import BusinessCoordinator
from business_agents.gateway.estimate_safety_gate import EstimateDraftSafetyGate
from business_agents.gateway.receipt_store import JsonlReceiptStore


def estimate_context() -> dict[str, object]:
    return {
        "estimate_id": "EST-0001",
        "job_id": "JOB-0001",
        "job_status": "estimating",
        "currency": "CAD",
        "labour_hours": "10",
        "labour_rate": "120.00",
        "materials_subtotal": "2500.00",
        "contingency_rate": "0.10",
        "margin_rate": "0.20",
        "tax_rate": "0.05",
        "notes": "Internal draft only",
    }


def test_estimate_agent_calculates_deterministic_total() -> None:
    proposal = EstimateAgent().propose(estimate_context())

    assert proposal.intent.parameters["labour_subtotal"] == "1200.00"
    assert proposal.intent.parameters["contingency_amount"] == "370.00"
    assert proposal.intent.parameters["margin_amount"] == "814.00"
    assert proposal.intent.parameters["tax_amount"] == "244.20"
    assert proposal.intent.parameters["total"] == "5128.20"


def test_estimate_requires_estimating_job() -> None:
    context = estimate_context()
    context["job_status"] = "approved"

    with pytest.raises(ValueError, match="job must be in estimating status"):
        EstimateAgent().propose(context)


def test_rates_are_bounded_between_zero_and_one() -> None:
    context = estimate_context()
    context["margin_rate"] = "1.25"

    with pytest.raises(ValueError, match="between 0 and 1"):
        EstimateAgent().propose(context)


def test_money_rejects_negative_or_non_finite_values() -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        money("-1")
    with pytest.raises(ValueError, match="finite and non-negative"):
        money("NaN")


def test_estimate_draft_validates_component_total() -> None:
    with pytest.raises(ValueError, match="does not match components"):
        EstimateDraft(
            estimate_id="EST-0001",
            job_id="JOB-0001",
            currency="CAD",
            labour_subtotal=Decimal("100.00"),
            materials_subtotal=Decimal("100.00"),
            contingency_amount=Decimal("0.00"),
            margin_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total=Decimal("201.00"),
        )


def test_safety_gate_rejects_tampered_total() -> None:
    proposal = EstimateAgent().propose(estimate_context())
    tampered = BusinessIntent(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "total": "1.00"},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )

    decision = EstimateDraftSafetyGate().evaluate(tampered)

    assert decision.passed is False
    assert decision.reason == "estimate-total-mismatch"


def test_safety_gate_rejects_external_send_fields() -> None:
    proposal = EstimateAgent().propose(estimate_context())
    unsafe = BusinessIntent(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "send_quote": True},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )

    decision = EstimateDraftSafetyGate().evaluate(unsafe)

    assert decision.passed is False
    assert decision.reason == "external-action-fields-forbidden"


def test_estimate_store_rejects_duplicate_id(tmp_path: Path) -> None:
    store = JsonlEstimateStore(tmp_path / "estimates.jsonl")
    proposal = EstimateAgent().propose(estimate_context())
    params = proposal.intent.parameters
    draft = EstimateDraft(
        estimate_id=str(params["estimate_id"]),
        job_id=str(params["job_id"]),
        currency=str(params["currency"]),
        labour_subtotal=money(params["labour_subtotal"]),
        materials_subtotal=money(params["materials_subtotal"]),
        contingency_amount=money(params["contingency_amount"]),
        margin_amount=money(params["margin_amount"]),
        tax_amount=money(params["tax_amount"]),
        total=money(params["total"]),
    )
    store.create(draft)

    with pytest.raises(ValueError, match="record already exists for estimate_id"):
        store.create(draft)


def test_approved_estimate_flow_is_durable_receipted_and_draft_only(tmp_path: Path) -> None:
    receipt_store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    estimate_store = JsonlEstimateStore(tmp_path / "estimates.jsonl")
    executor = EstimateExecutor(estimate_store, receipt_store)
    coordinator = BusinessCoordinator(
        court=CourtPolicy(),
        safety_gate=EstimateDraftSafetyGate(),
        executor_registry=ExecutorRegistry([executor]),
        receipt_store=receipt_store,
    )

    result = coordinator.run(
        EstimateAgent(),
        estimate_context(),
        identity_verified=True,
    )

    assert result.status == "completed"
    assert result.output["total"] == "5128.20"
    assert result.output["draft_only"] is True
    stored = estimate_store.get("EST-0001")
    assert stored is not None
    assert stored.total == Decimal("5128.20")
    assert result.receipt_id
