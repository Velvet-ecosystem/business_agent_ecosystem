from business_agents.agents.inventory_agent import InventoryAgent
from business_agents.gateway.authority import CourtPolicy


class FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def proposal():
    return InventoryAgent().propose(
        {
            "sku": "FILTER-001",
            "location": "small-workshop",
            "on_hand": 2,
            "reorder_point": 8,
            "suggested_quantity": 12,
        }
    )


def test_authorization_expires_at_deadline() -> None:
    clock = FakeClock()
    court = CourtPolicy(grant_ttl_seconds=5.0, clock=clock)
    item = proposal()
    decision = court.evaluate(item, identity_verified=True, safety_passed=True)

    assert decision.issued_at == 1000.0
    assert decision.expires_at == 1005.0
    assert decision.authorization_id is not None

    clock.advance(5.0)
    assert court.consume_authorization(decision.authorization_id, item.intent) is False


def test_cleanup_removes_expired_grants() -> None:
    clock = FakeClock()
    court = CourtPolicy(grant_ttl_seconds=10.0, clock=clock)
    item = proposal()
    first = court.evaluate(item, identity_verified=True, safety_passed=True)

    clock.advance(6.0)
    second = court.evaluate(item, identity_verified=True, safety_passed=True)
    assert court.active_grant_count == 2

    clock.advance(4.0)
    assert court.cleanup_expired() == 1
    assert court.active_grant_count == 1
    assert second.authorization_id is not None
    assert court.consume_authorization(second.authorization_id, item.intent) is True
    assert first.authorization_id is not None
    assert court.consume_authorization(first.authorization_id, item.intent) is False


def test_non_positive_ttl_is_rejected() -> None:
    try:
        CourtPolicy(grant_ttl_seconds=0)
    except ValueError as exc:
        assert "must be positive" in str(exc)
    else:
        raise AssertionError("zero TTL should be rejected")
