from pathlib import Path

import pytest

from business_agents.approval_requests import (
    ApprovalRequest,
    ApprovalRequestStatus,
    ApprovalRequestStore,
)
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.skills.approval_attention_queue import ApprovalAttentionQueueSkill


def _request(
    request_id: str,
    risk_level: RiskLevel,
    approval_mode: ApprovalMode,
    status: ApprovalRequestStatus = ApprovalRequestStatus.PENDING,
) -> ApprovalRequest:
    return ApprovalRequest(
        request_id=request_id,
        route="jobs.transition",
        action="transition",
        subject_id=f"job-{request_id}",
        summary=f"Review {request_id}",
        requested_by="test-agent",
        risk_level=risk_level,
        approval_mode=approval_mode,
        status=status,
    )


def test_approval_request_rejects_unsafe_approval_mode() -> None:
    with pytest.raises(ValueError, match="high-risk approval requests"):
        _request("req-unsafe", RiskLevel.HIGH, ApprovalMode.POLICY)


def test_approval_attention_queue_is_read_only_and_pending_only(tmp_path: Path) -> None:
    path = tmp_path / "approvals.jsonl"
    store = ApprovalRequestStore(path)
    store.create(_request("req-002", RiskLevel.HIGH, ApprovalMode.STRONG_HUMAN))
    store.create(_request("req-001", RiskLevel.MEDIUM, ApprovalMode.HUMAN))
    store.create(
        _request(
            "req-003",
            RiskLevel.LOW,
            ApprovalMode.POLICY,
            ApprovalRequestStatus.CANCELLED,
        )
    )

    before = path.read_text(encoding="utf-8")
    result = ApprovalAttentionQueueSkill(store).run({})
    after = path.read_text(encoding="utf-8")

    assert result.output == {
        "pending_count": 2,
        "risk_counts": {"high": 1, "medium": 1},
        "approval_mode_counts": {"human": 1, "strong-human": 1},
        "requests": (
            {
                "request_id": "req-001",
                "route": "jobs.transition",
                "action": "transition",
                "subject_id": "job-req-001",
                "summary": "Review req-001",
                "risk_level": "medium",
                "approval_mode": "human",
            },
            {
                "request_id": "req-002",
                "route": "jobs.transition",
                "action": "transition",
                "subject_id": "job-req-002",
                "summary": "Review req-002",
                "risk_level": "high",
                "approval_mode": "strong-human",
            },
        ),
    }
    assert before == after
    assert "requested_by" not in repr(result.output)


def test_approval_attention_queue_rejects_inputs(tmp_path: Path) -> None:
    skill = ApprovalAttentionQueueSkill(ApprovalRequestStore(tmp_path / "approvals.jsonl"))

    with pytest.raises(ValueError, match="accepts no inputs"):
        skill.run({"decision": "approve"})


def test_store_rejects_duplicate_request_ids(tmp_path: Path) -> None:
    store = ApprovalRequestStore(tmp_path / "approvals.jsonl")
    request = _request("req-001", RiskLevel.MEDIUM, ApprovalMode.HUMAN)
    store.create(request)

    with pytest.raises(ValueError):
        store.create(request)
