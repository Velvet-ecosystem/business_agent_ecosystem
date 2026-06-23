"""Tests for work-start proposal validation."""

import pytest

from business_agents.agents.work_start_agent import WorkStartAgent
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.gateway.work_start_safety_gate import WorkStartSafetyGate


def context() -> dict[str, str]:
    return {
        "start_id": "START-0001",
        "job_id": "JOB-0001",
        "booking_id": "BOOK-0001",
        "started_by": "Mister",
        "reason": "Vehicle and work bay are ready.",
        "job_status": "scheduled",
    }


def test_work_start_requires_strong_human_approval() -> None:
    proposal = WorkStartAgent().propose(context())
    assert proposal.intent.risk_level is RiskLevel.HIGH
    assert proposal.intent.approval_mode is ApprovalMode.STRONG_HUMAN


def test_work_start_requires_scheduled_job() -> None:
    invalid = context()
    invalid["job_status"] = "ready-to-schedule"
    with pytest.raises(ValueError, match="scheduled"):
        WorkStartAgent().propose(invalid)


def test_gate_rejects_extra_fields() -> None:
    proposal = WorkStartAgent().propose(context())
    intent_type = type(proposal.intent)
    altered = intent_type(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "extra": "not allowed"},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )
    decision = WorkStartSafetyGate().evaluate(altered)
    assert decision.passed is False
    assert decision.reason == "unexpected-work-start-fields"
