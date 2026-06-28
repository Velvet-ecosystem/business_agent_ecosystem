from business_agents.capability_registry import CAPABILITIES, capability_for_identity


def test_capability_identities_are_unique() -> None:
    identities = [(item.route, item.action) for item in CAPABILITIES]
    assert len(identities) == len(set(identities))


def test_identity_lookup_requires_route_and_action() -> None:
    item = capability_for_identity("communication-history", "record-communication-reference")
    assert item is not None
    assert item.route == "communication-history"
    assert capability_for_identity("communication-history", "record-report-snapshot") is None
    assert capability_for_identity("missing-route", "record-communication-reference") is None
