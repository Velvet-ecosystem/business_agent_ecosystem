import pytest

from business_agents.contracts import ApprovalMode, RiskLevel
from business_agents.gateway.authority import CourtPolicy, intent_fingerprint
from business_agents.procurement_intents import (
    PROCUREMENT_ACTION,
    PROCUREMENT_ROUTE,
    build_procurement_intent,
    validate_procurement_lineage,
)


def lineage(**changes):
    values = {
        "approval_request_id": "approval-001",
        "decision_id": "decision-001",
        "artifact_id": "artifact-001",
        "artifact_digest": "a" * 64,
        "route": PROCUREMENT_ROUTE,
        "action": PROCUREMENT_ACTION,
        "subject_id": "artifact-001",
        "risk_level": "high",
        "approval_mode": "strong-human",
        "bounded_to_exact_artifact_digest": True,
    }
    values.update(changes)
    return values


def test_builder_creates_strong_human_high_risk_intent():
    intent = build_procurement_intent(lineage(), handler_id="handler-001")

    assert intent.route == PROCUREMENT_ROUTE
    assert intent.action == PROCUREMENT_ACTION
    assert intent.subject_id == "artifact-001"
    assert intent.risk_level is RiskLevel.HIGH
    assert intent.approval_mode is ApprovalMode.STRONG_HUMAN
    assert intent.parameters == {
        "artifact_id": "artifact-001",
        "artifact_digest": "a" * 64,
        "handler_id": "handler-001",
        "approval_request_id": "approval-001",
        "decision_id": "decision-001",
        "lineage_route": PROCUREMENT_ROUTE,
        "lineage_action": PROCUREMENT_ACTION,
        "lineage_subject_id": "artifact-001",
    }


def test_builder_rejects_drifted_lineage_fields():
    with pytest.raises(ValueError, match="subject_id"):
        build_procurement_intent(lineage(subject_id="artifact-002"), handler_id="handler-001")
    with pytest.raises(ValueError, match="route"):
        build_procurement_intent(lineage(route="other.route"), handler_id="handler-001")
    with pytest.raises(ValueError, match="action"):
        build_procurement_intent(lineage(action="other-action"), handler_id="handler-001")
    with pytest.raises(ValueError, match="digest"):
        build_procurement_intent(lineage(artifact_digest="A" * 64), handler_id="handler-001")


def test_builder_rejects_missing_or_weak_lineage():
    weak = lineage(approval_mode="human")
    with pytest.raises(ValueError, match="strong-human"):
        build_procurement_intent(weak, handler_id="handler-001")
    unbound = lineage(bounded_to_exact_artifact_digest=False)
    with pytest.raises(ValueError, match="exact artifact digest"):
        build_procurement_intent(unbound, handler_id="handler-001")
    missing = lineage()
    del missing["decision_id"]
    with pytest.raises(ValueError, match="missing"):
        validate_procurement_lineage(missing)


def test_handler_and_digest_are_part_of_court_fingerprint():
    intent = build_procurement_intent(lineage(), handler_id="handler-001")
    changed_handler = build_procurement_intent(lineage(), handler_id="handler-002")
    changed_digest = build_procurement_intent(lineage(artifact_digest="b" * 64), handler_id="handler-001")

    assert intent_fingerprint(intent) != intent_fingerprint(changed_handler)
    assert intent_fingerprint(intent) != intent_fingerprint(changed_digest)


def test_intent_can_use_existing_court_without_extra_authority():
    court = CourtPolicy()
    intent = build_procurement_intent(lineage(), handler_id="handler-001")
    decision = court.evaluate(
        proposal=type(
            "Proposal",
            (),
            {
                "intent": intent,
            },
        )(),
        identity_verified=True,
        safety_passed=True,
        principal_id="principal-001",
        session_id="session-001",
    )

    assert decision.approved
    assert decision.authorization_id is not None
    assert court.consume_authorization(
        decision.authorization_id,
        intent,
        principal_id="principal-001",
        session_id="session-001",
    )
