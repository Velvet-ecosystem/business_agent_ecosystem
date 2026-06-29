from importlib import import_module

from business_agents.capability_registry import CAPABILITIES


def test_registered_gate_and_executor_modules_are_importable() -> None:
    for item in CAPABILITIES:
        assert import_module(item.gate_module) is not None
        assert import_module(item.executor_module) is not None


def test_registered_module_paths_remain_inside_business_agents() -> None:
    for item in CAPABILITIES:
        assert item.gate_module.startswith("business_agents.")
        assert item.executor_module.startswith("business_agents.")
