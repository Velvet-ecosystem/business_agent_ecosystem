from pathlib import Path

import pytest

from business_agents.approval_decisions import ApprovalDecisionStore
from business_agents.approval_requests import ApprovalRequest, ApprovalRequestStore
from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.skills.record_approval_decision import RecordApprovalDecisionSkill


def _build_skill(tmp_path: Path) -> tuple[RecordApprovalDecisionSkill, ApprovalDecisionStore]:
    requests = ApprovalRequestStore(tmp_path / "requests.jsonl")
    decisions = ApprovalDecisionStore(tmp_path / "decisions.jsonl")
    requests.create(
        ApprovalRequest(
            request_id="approval-001",
            route="procurement.order",
            action="place-bounded-order",
            subject_id="req-001",
            summary="Review purchase",
            requested_by="procurement-agent",
            risk_level=RiskLevel.HIGH,
            approval_mode=ApprovalMode.STRONG_HUMAN,
        )
    )
    return RecordApprovalDecisionSkill(requests, decisions), decisions


def test_record_approval_decision_grants_no_authority(tmp_path: Path) -> None:
    skill, decisions = _build_skill(tmp_path)

    result = skill.run(
        {
            "decision_id": "decision-001",
            "request_id": "approval-001",
            "decision": "approve",
            "decided_by": "Mister",
            "rationale": "Terms reviewed and accepted.",
            "strong_confirmation": True,
        }
    )

    assert result.output["decision"]["decision"] == "approve"
    assert result.output["decision"]["strong_confirmation"] is True
    assert result.output["court_authority"] is False
    assert result.output["execution_authority"] is False
    assert decisions.get_for_request("approval-001") is not None


def test_approval_requires_strong_confirmation(tmp_path: Path) -> None:
    skill, decisions = _build_skill(tmp_path)

    with pytest.raises(ValueError, match="strong confirmation"):
        skill.run(
            {
                "decision_id": "decision-001",
                "request_id": "approval-001",
                "decision": "approve",
                "decided_by": "Mister",
                "rationale": "Reviewed.",
                "strong_confirmation": False,
            }
        )
    assert decisions.get_for_request("approval-001") is None


def test_denial_does_not_require_strong_confirmation(tmp_path: Path) -> None:
    skill, decisions = _build_skill(tmp_path)

    result = skill.run(
        {
            "decision_id": "decision-001",
            "request_id": "approval-001",
            "decision": "deny",
            "decided_by": "Mister",
            "rationale": "Supplier risk is unacceptable.",
            "strong_confirmation": False,
        }
    )

    assert result.output["decision"]["decision"] == "deny"
    assert decisions.get_for_request("approval-001") is not None


def test_duplicate_decision_is_rejected(tmp_path: Path) -> None:
    skill, _ = _build_skill(tmp_path)
    inputs = {
        "decision_id": "decision-001",
        "request_id": "approval-001",
        "decision": "deny",
        "decided_by": "Mister",
        "rationale": "Denied.",
        "strong_confirmation": False,
    }
    skill.run(inputs)

    with pytest.raises(ValueError, match="decision already exists"):
        skill.run({**inputs, "decision_id": "decision-002"})


def test_missing_request_is_rejected(tmp_path: Path) -> None:
    requests = ApprovalRequestStore(tmp_path / "requests.jsonl")
    decisions = ApprovalDecisionStore(tmp_path / "decisions.jsonl")
    skill = RecordApprovalDecisionSkill(requests, decisions)

    with pytest.raises(ValueError, match="approval request not found"):
        skill.run(
            {
                "decision_id": "decision-001",
                "request_id": "missing",
                "decision": "deny",
                "decided_by": "Mister",
                "rationale": "No matching request.",
                "strong_confirmation": False,
            }
        )


def test_extra_execution_input_is_rejected(tmp_path: Path) -> None:
    skill, decisions = _build_skill(tmp_path)

    with pytest.raises(ValueError, match="exact declared inputs"):
        skill.run(
            {
                "decision_id": "decision-001",
                "request_id": "approval-001",
                "decision": "approve",
                "decided_by": "Mister",
                "rationale": "Reviewed.",
                "strong_confirmation": True,
                "execute": True,
            }
        )
    assert decisions.get_for_request("approval-001") is None
