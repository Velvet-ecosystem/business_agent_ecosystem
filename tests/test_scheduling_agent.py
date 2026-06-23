"""Tests for scheduling proposal validation."""

import pytest

from business_agents.agents.scheduling_agent import SchedulingAgent
from business_agents.gateway.schedule_proposal_safety_gate import ScheduleProposalSafetyGate


def schedule_context() -> dict[str, object]:
    return {
        "proposal_id": "SCH-0001",
        "job_id": "JOB-0001",
        "job_status": "ready-to-schedule",
        "timezone": "America/Edmonton",
        "windows": [
            {"start": "2026-07-02T09:00:00-06:00", "end": "2026-07-02T12:00:00-06:00"},
            {"start": "2026-07-03T13:00:00-06:00", "end": "2026-07-03T17:00:00-06:00"},
        ],
        "notes": "Internal candidates only",
    }


def test_agent_requires_ready_to_schedule_job() -> None:
    context = schedule_context()
    context["job_status"] = "estimating"
    with pytest.raises(ValueError, match="ready-to-schedule"):
        SchedulingAgent().propose(context)


def test_agent_rejects_overlapping_windows() -> None:
    context = schedule_context()
    context["windows"] = [
        {"start": "2026-07-02T09:00:00-06:00", "end": "2026-07-02T12:00:00-06:00"},
        {"start": "2026-07-02T11:00:00-06:00", "end": "2026-07-02T13:00:00-06:00"},
    ]
    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        SchedulingAgent().propose(context)


def test_agent_rejects_naive_times() -> None:
    context = schedule_context()
    context["windows"] = [
        {"start": "2026-07-02T09:00:00", "end": "2026-07-02T12:00:00"},
    ]
    with pytest.raises(ValueError, match="timezone offsets"):
        SchedulingAgent().propose(context)


def test_safety_gate_rejects_extra_fields() -> None:
    proposal = SchedulingAgent().propose(schedule_context())
    intent_type = type(proposal.intent)
    altered = intent_type(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "extra": "not allowed"},
        risk_level=proposal.intent.risk_level,
        approval_mode=proposal.intent.approval_mode,
    )
    decision = ScheduleProposalSafetyGate().evaluate(altered)
    assert decision.passed is False
    assert decision.reason == "unexpected-schedule-fields"
