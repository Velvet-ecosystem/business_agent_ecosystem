from business_agents.capability_registry import CAPABILITIES


def test_registered_capabilities_remain_local_only() -> None:
    assert CAPABILITIES
    assert all(item.external_action is False for item in CAPABILITIES)


def test_registered_approval_modes_remain_bounded() -> None:
    allowed_modes = {"human", "strong-human"}
    assert all(item.approval_mode in allowed_modes for item in CAPABILITIES)
