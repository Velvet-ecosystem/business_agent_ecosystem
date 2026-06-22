"""Route-aware safety-gate registry."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from business_agents.contracts import BusinessIntent
from business_agents.gateway.safety_gate import SafetyDecision


class SafetyGate(Protocol):
    route: str

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        """Evaluate one intent for a specific route."""


class SafetyGateRegistry:
    """Resolves and applies the safety gate for an intent route."""

    def __init__(self, gates: Iterable[SafetyGate] = ()) -> None:
        self._gates: dict[str, SafetyGate] = {}
        for gate in gates:
            self.register(gate)

    def register(self, gate: SafetyGate) -> None:
        route = gate.route.strip()
        if not route:
            raise ValueError("safety gate route is required")
        if route in self._gates:
            raise ValueError(f"safety gate route already registered: {route}")
        self._gates[route] = gate

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        gate = self._gates.get(intent.route)
        if gate is None:
            return SafetyDecision(False, "unsupported-route")
        return gate.evaluate(intent)

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(sorted(self._gates))
