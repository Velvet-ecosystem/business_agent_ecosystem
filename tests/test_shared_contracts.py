"""Tests for shared agent, intent, handoff, and executor contracts."""

import pytest

from business_agents.contracts import (
    AgentHandoff,
    AgentProposal,
    ApprovalMode,
    BusinessIntent,
    ExecutorResult,
    RiskLevel,
)


def test_existing_low_risk_intent_defaults_remain_compatible() -> None:
    intent = BusinessIntent(
        route="internal-task",
        action="create-restock-review",
        subject_id="small-workshop",
    )

    assert intent.risk_level is RiskLevel.LOW
    assert intent.approval_mode is ApprovalMode.POLICY


def test_high_risk_intent_requires_human_approval() -> None:
    with pytest.raises(ValueError, match="high-risk intents"):
        BusinessIntent(
            route="purchasing",
            action="place-order",
            subject_id="supplier-1",
            risk_level=RiskLevel.HIGH,
        )


def test_critical_intent_requires_strong_human_approval() -> None:
    with pytest.raises(ValueError, match="critical intents"):
        BusinessIntent(
            route="treasury",
            action="change-payout-account",
            subject_id="business-account",
            risk_level=RiskLevel.CRITICAL,
            approval_mode=ApprovalMode.HUMAN,
        )


def test_critical_intent_accepts_strong_human_approval() -> None:
    intent = BusinessIntent(
        route="treasury",
        action="change-payout-account",
        subject_id="business-account",
        risk_level=RiskLevel.CRITICAL,
        approval_mode=ApprovalMode.STRONG_HUMAN,
    )

    assert intent.approval_mode is ApprovalMode.STRONG_HUMAN


def test_agent_proposal_cannot_grant_its_own_authority() -> None:
    intent = BusinessIntent("internal-task", "create", "job-1")

    with pytest.raises(ValueError, match="cannot grant authority"):
        AgentProposal(
            agent_name="Intake Agent",
            intent=intent,
            rationale="A follow-up task is required.",
            confidence=0.9,
            authority_granted=True,
        )


def test_handoff_requires_distinct_agents() -> None:
    with pytest.raises(ValueError, match="cannot hand work to itself"):
        AgentHandoff(
            source_agent="Intake Agent",
            target_agent="Intake Agent",
            purpose="Estimate the captured request",
        )


def test_handoff_carries_bounded_context() -> None:
    handoff = AgentHandoff(
        source_agent="Intake Agent",
        target_agent="Estimator Agent",
        purpose="Prepare an estimate draft",
        context={"job_id": "JOB-001", "vehicle": "2008 Hyundai Tiburon"},
    )

    assert handoff.context["job_id"] == "JOB-001"


def test_executor_result_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="unsupported executor result status"):
        ExecutorResult(
            executor_name="Task Executor",
            status="sort-of-done",
            receipt_id="receipt-1",
        )
