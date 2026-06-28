from business_agents.capability_registry import CAPABILITIES, capability_for_route


def test_routes_are_unique_and_bounded() -> None:
    routes = [item.route for item in CAPABILITIES]
    assert len(routes) == len(set(routes))
    assert routes
    for item in CAPABILITIES:
        assert item.approval_mode in {"human", "strong-human"}
        assert item.gate_module
        assert item.executor_module
        assert item.external_action is False


def test_registry_lookup() -> None:
    assert capability_for_route("communication-history") is not None
    assert capability_for_route("missing-route") is None
