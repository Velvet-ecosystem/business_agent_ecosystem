"""Tests for booking proposal approval requirements."""

import pytest

from business_agents.agents.booking_agent import BookingAgent
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.gateway.booking_safety_gate import BookingSafetyGate


def valid_context() -> dict[str, str]:
    return {
        "booking_id": "BOOK-0001",
        "job_id": "JOB-0001",
        "preparation_id": "PREP-0001",
        "idempotency_key": "book-JOB-0001-PREP-0001",
        "job_status": "ready-to-schedule",
        "title": "Velvet installation",
        "description": "Approved workshop booking",
    }


def test_booking_is_high_risk_and_strong_human() -> None:
    proposal = BookingAgent().propose(valid_context())
    assert proposal.intent.risk_level is RiskLevel.HIGH
    assert proposal.intent.approval_mode is ApprovalMode.STRONG_HUMAN
    assert proposal.authority_granted is False


def test_booking_requires_ready_job() -> None:
    context = valid_context()
    context["job_status"] = "estimating"
    with pytest.raises(ValueError, match="ready-to-schedule"):
        BookingAgent().propose(context)


def test_booking_gate_rejects_extra_field() -> None:
    proposal = BookingAgent().propose(valid_context())
    intent_type = type(proposal.intent)
    altered = intent_type(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "extra": "not allowed"},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )
    decision = BookingSafetyGate().evaluate(altered)
    assert decision.passed is False
    assert decision.reason == "unexpected-booking-fields"
