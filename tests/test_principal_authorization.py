from business_agents.agents.inventory_agent import InventoryAgent
from business_agents.gateway.authority import CourtPolicy


def proposal():
    return InventoryAgent().propose({
        "sku": "FILTER-001",
        "location": "small-workshop",
        "on_hand": 2,
        "reorder_point": 8,
        "suggested_quantity": 12,
    })


def test_principal_bound_grant_consumes_for_same_session() -> None:
    court = CourtPolicy()
    item = proposal()
    decision = court.evaluate(
        item,
        identity_verified=True,
        safety_passed=True,
        principal_id="owner-1",
        session_id="session-1",
    )
    assert court.consume_authorization(
        decision.authorization_id,
        item.intent,
        principal_id="owner-1",
        session_id="session-1",
    ) is True


def test_principal_bound_grant_rejects_actor_drift() -> None:
    court = CourtPolicy()
    item = proposal()
    decision = court.evaluate(
        item,
        identity_verified=True,
        safety_passed=True,
        principal_id="owner-1",
        session_id="session-1",
    )
    assert court.consume_authorization(
        decision.authorization_id,
        item.intent,
        principal_id="owner-2",
        session_id="session-1",
    ) is False


def test_principal_bound_grant_rejects_session_drift() -> None:
    court = CourtPolicy()
    item = proposal()
    decision = court.evaluate(
        item,
        identity_verified=True,
        safety_passed=True,
        principal_id="owner-1",
        session_id="session-1",
    )
    assert court.consume_authorization(
        decision.authorization_id,
        item.intent,
        principal_id="owner-1",
        session_id="session-2",
    ) is False


def test_legacy_unbound_grants_remain_compatible() -> None:
    court = CourtPolicy()
    item = proposal()
    decision = court.evaluate(item, identity_verified=True, safety_passed=True)
    assert court.consume_authorization(decision.authorization_id, item.intent) is True
