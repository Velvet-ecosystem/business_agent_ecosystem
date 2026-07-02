from pathlib import Path

import pytest

from business_agents.approval_decisions import (
    ApprovalDecision,
    ApprovalDecisionStore,
    ApprovalDecisionValue,
)
from business_agents.approval_requests import ApprovalRequest, ApprovalRequestStore
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.skills.prepare_decision_lineage import PrepareDecisionLineageSkill


def _stores(tmp_path: Path) -> tuple[ApprovalRequestStore, ApprovalDecisionStore]:
    return (
        ApprovalRequestStore(tmp_path / "requests.jsonl"),
        ApprovalDecisionStore(tmp_path / "decisions.jsonl"),
    )


def _request() -> ApprovalRequest:
    return ApprovalRequest(
        request_id="approval-001",
        route="procurement.order",
        action="place-bounded-order",
        subject_id="req-001",
        summary="Review purchase",
        requested_by="procurement-agent",
        risk_level=RiskLevel.HIGH,
        approval_mode=ApprovalMode.STRONG_HUMAN,
    )


def _decision(value: ApprovalDecisionValue, strong: bool) -> ApprovalDecision:
    return ApprovalDecision(
        decision_id="decision-001",
        request_id="approval-001",
        decision=value,
        decided_by="Mister",
        rationale="Reviewed against the prepared package.",
        strong_confirmation=strong,
    )


def test_lineage_package_binds_exact_scope_without_authority(tmp_path: Path) -> None:
    requests, decisions = _stores(tmp_path)
    requests.create(_request())
    decisions.create(_decision(ApprovalDecisionValue.APPROVE, True))

    result = PrepareDecisionLineageSkill(requests, decisions).run(
        {"request_id": "approval-001"}
    )

    assert result.output["lineage_package"] == {
        "approval_request_id": "approval-001",
        "decision_id": "decision-001",
        "route": "procurement.order",
        "action": "place-bounded-order",
        "subject_id": "req-001",
        "risk_level": "high",
        "approval_mode": "strong-human",
        "decided_by": "Mister",
        "decision_rationale": "Reviewed against the prepared package.",
        "single_use_requested": True,
        "bounded_to_exact_route_action_subject": True,
    }
    assert result.output["authority_granted"] is False
    assert result.output["action_performed"] is False


def test_denied_decision_is_rejected(tmp_path: Path) -> None:
    requests, decisions = _stores(tmp_path)
    requests.create(_request())
    decisions.create(_decision(ApprovalDecisionValue.DENY, False))

    with pytest.raises(ValueError, match="not approved"):
        PrepareDecisionLineageSkill(requests, decisions).run(
            {"request_id": "approval-001"}
        )


def test_missing_decision_is_rejected(tmp_path: Path) -> None:
    requests, decisions = _stores(tmp_path)
    requests.create(_request())

    with pytest.raises(ValueError, match="decision not found"):
        PrepareDecisionLineageSkill(requests, decisions).run(
            {"request_id": "approval-001"}
        )


def test_missing_request_is_rejected(tmp_path: Path) -> None:
    requests, decisions = _stores(tmp_path)

    with pytest.raises(ValueError, match="request not found"):
        PrepareDecisionLineageSkill(requests, decisions).run(
            {"request_id": "missing"}
        )


def test_extra_action_input_is_rejected(tmp_path: Path) -> None:
    requests, decisions = _stores(tmp_path)
    requests.create(_request())
    decisions.create(_decision(ApprovalDecisionValue.APPROVE, True))

    with pytest.raises(ValueError, match="requires only request_id"):
        PrepareDecisionLineageSkill(requests, decisions).run(
            {"request_id": "approval-001", "perform": True}
        )
