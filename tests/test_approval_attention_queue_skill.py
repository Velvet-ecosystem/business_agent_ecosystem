from pathlib import Path

import pytest

from business_agents.approval_decisions import ApprovalDecision, ApprovalDecisionStore, ApprovalDecisionValue
from business_agents.approval_requests import ApprovalRequest, ApprovalRequestStore
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.skills.approval_attention_queue import ApprovalAttentionQueueSkill


def make_request(request_id: str) -> ApprovalRequest:
    return ApprovalRequest(
        request_id=request_id,
        route="example.route",
        action="example-action",
        subject_id=f"subject-{request_id}",
        summary=f"Review {request_id}",
        requested_by="test-agent",
        risk_level=RiskLevel.HIGH,
        approval_mode=ApprovalMode.STRONG_HUMAN,
    )


def make_decision(request_id: str, value: ApprovalDecisionValue) -> ApprovalDecision:
    return ApprovalDecision(
        decision_id=f"decision-{request_id}",
        request_id=request_id,
        decision=value,
        decided_by="Mister",
        rationale="Reviewed.",
        strong_confirmation=value is ApprovalDecisionValue.APPROVE,
    )


def test_queue_separates_pending_from_decided(tmp_path: Path) -> None:
    request_path = tmp_path / "requests.jsonl"
    decision_path = tmp_path / "decisions.jsonl"
    requests = ApprovalRequestStore(request_path)
    decisions = ApprovalDecisionStore(decision_path)
    for request_id in ("req-001", "req-002", "req-003"):
        requests.create(make_request(request_id))
    decisions.create(make_decision("req-002", ApprovalDecisionValue.APPROVE))
    decisions.create(make_decision("req-003", ApprovalDecisionValue.DENY))

    before_requests = request_path.read_text(encoding="utf-8")
    before_decisions = decision_path.read_text(encoding="utf-8")
    result = ApprovalAttentionQueueSkill(requests, decisions).run({})

    assert result.output["pending_count"] == 1
    assert result.output["decided_count"] == 2
    assert result.output["state_counts"] == {"approve": 1, "deny": 1, "pending": 1}
    assert [item["review_state"] for item in result.output["requests"]] == ["pending", "approve", "deny"]
    assert result.output["requests"][0]["decision_id"] is None
    assert result.output["requests"][1]["decision_id"] == "decision-req-002"
    assert request_path.read_text(encoding="utf-8") == before_requests
    assert decision_path.read_text(encoding="utf-8") == before_decisions


def test_queue_rejects_inputs(tmp_path: Path) -> None:
    skill = ApprovalAttentionQueueSkill(
        ApprovalRequestStore(tmp_path / "requests.jsonl"),
        ApprovalDecisionStore(tmp_path / "decisions.jsonl"),
    )
    with pytest.raises(ValueError, match="accepts no inputs"):
        skill.run({"extra": True})
