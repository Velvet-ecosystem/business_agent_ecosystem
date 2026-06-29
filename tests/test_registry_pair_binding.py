from importlib import import_module
from inspect import getmembers, isclass

from business_agents.capability_registry import CAPABILITIES
from business_agents.executors.base_executor import BaseExecutor


def test_registered_executor_modules_bind_declared_route_and_action() -> None:
    for item in CAPABILITIES:
        module = import_module(item.executor_module)
        executors = [
            cls
            for _, cls in getmembers(module, isclass)
            if issubclass(cls, BaseExecutor) and cls is not BaseExecutor
        ]
        assert any(
            cls.route == item.route and item.action in cls.allowed_actions
            for cls in executors
        )
