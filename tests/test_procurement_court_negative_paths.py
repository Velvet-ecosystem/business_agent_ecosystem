from business_agents.contracts import AgentProposal, ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.authority import CourtPolicy


class Clock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value


def make_intent(**changes) -> BusinessIntent:
    values = {
        "route": "procurement.order",
        "action": "place-bounded-order",
        "subject_id": "artifact-001",
        "parameters": {
            "artifact_id": "artifact-001",
            "artifact_digest": "a" * 64,
            "handler_id": "handler-001",
            "approval_request_id": "approval-001",
            "decision_id": "decision-001",
        },
        "risk_level": RiskLevel.HIGH,
        "approval_mode": ApprovalMode.STRONG_HUMAN,
    }
    values.update(changes)
    return BusinessIntent(**values)


def proposal(intent: BusinessIntent) -> AgentProposal:
    return AgentProposal(
        agent_name="procurement-agent",
        intent=intent,
        rationale="Use the reviewed immutable artifact.",
        confidence=1.0,
    )


def authorize(court: CourtPolicy, intent: BusinessIntent):
    return court.evaluate(
        proposal(intent),
        identity_verified=True,
        safety_passed=True,
        principal_id="principal-001",
        session_id="session-001",
    )


def test_court_denies_missing_identity_or_safety() -> None:
    court = CourtPolicy()
    intent = make_intent()

    missing_identity = court.evaluate(
        proposal(intent), identity_verified=False, safety_passed=True
    )
    failed_safety = court.evaluate(
        proposal(intent), identity_verified=True, safety_passed=False
    )

    assert not missing_identity.approved
    assert missing_identity.reason == "identity-not-verified"
    assert not failed_safety.approved
    assert failed_safety.reason == "safety-check-failed"
    assert court.active_grant_count == 0


def test_digest_drift_invalidates_grant() -> None:
    court = CourtPolicy()
    intent = make_intent()
    decision = authorize(court, intent)
    changed = make_intent(
        parameters={**dict(intent.parameters), "artifact_digest": "b" * 64}
    )

    assert decision.authorization_id is not None
    assert not court.consume_authorization(
        decision.authorization_id,
        changed,
        principal_id="principal-001",
        session_id="session-001",
    )


def test_route_and_handler_drift_invalidate_grants() -> None:
    court = CourtPolicy()
    intent = make_intent()
    route_decision = authorize(court, intent)
    route_changed = make_intent(route="procurement.changed")

    assert route_decision.authorization_id is not None
    assert not court.consume_authorization(
        route_decision.authorization_id,
        route_changed,
        principal_id="principal-001",
        session_id="session-001",
    )

    handler_decision = authorize(court, intent)
    handler_changed = make_intent(
        parameters={**dict(intent.parameters), "handler_id": "handler-002"}
    )
    assert handler_decision.authorization_id is not None
    assert not court.consume_authorization(
        handler_decision.authorization_id,
        handler_changed,
        principal_id="principal-001",
        session_id="session-001",
    )


def test_expired_grant_cannot_be_consumed() -> None:
    clock = Clock()
    court = CourtPolicy(grant_ttl_seconds=5.0, clock=clock)
    intent = make_intent()
    decision = authorize(court, intent)
    clock.value = 105.0

    assert decision.authorization_id is not None
    assert not court.consume_authorization(
        decision.authorization_id,
        intent,
        principal_id="principal-001",
        session_id="session-001",
    )


def test_grant_is_single_use_and_actor_bound() -> None:
    court = CourtPolicy()
    intent = make_intent()
    actor_decision = authorize(court, intent)

    assert actor_decision.authorization_id is not None
    assert not court.consume_authorization(
        actor_decision.authorization_id,
        intent,
        principal_id="principal-002",
        session_id="session-001",
    )

    replay_decision = authorize(court, intent)
    assert replay_decision.authorization_id is not None
    assert court.consume_authorization(
        replay_decision.authorization_id,
        intent,
        principal_id="principal-001",
        session_id="session-001",
    )
    assert not court.consume_authorization(
        replay_decision.authorization_id,
        intent,
        principal_id="principal-001",
        session_id="session-001",
    )
