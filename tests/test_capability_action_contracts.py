from importlib import import_module
from inspect import getmembers, isclass

from business_agents.capability_registry import CAPABILITIES


def executor_allowed_actions(module_name: str) -> set[str]:
    module = import_module(module_name)
    actions: set[str] = set()
    for _, candidate in getmembers(module, isclass):
        if candidate.__module__ != module.__name__:
            continue
        allowed = getattr(candidate, "allowed_actions", None)
        if isinstance(allowed, (set, frozenset)):
            actions.update(str(action) for action in allowed)
    return actions


def test_registered_executor_actions_match_registry() -> None:
    for item in CAPABILITIES:
        assert item.action.strip()
        assert executor_allowed_actions(item.executor_module) == {item.action}
