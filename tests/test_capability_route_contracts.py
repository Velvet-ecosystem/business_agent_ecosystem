from importlib import import_module
from inspect import getmembers, isclass

from business_agents.capability_registry import CAPABILITIES


def declared_routes(module_name: str) -> set[str]:
    module = import_module(module_name)
    routes: set[str] = set()
    for _, candidate in getmembers(module, isclass):
        if candidate.__module__ != module.__name__:
            continue
        route = getattr(candidate, "route", None)
        if isinstance(route, str) and route.strip():
            routes.add(route)
    return routes


def test_registered_gate_routes_match_registry() -> None:
    for item in CAPABILITIES:
        assert declared_routes(item.gate_module) == {item.route}


def test_registered_executor_routes_match_registry() -> None:
    for item in CAPABILITIES:
        assert declared_routes(item.executor_module) == {item.route}
