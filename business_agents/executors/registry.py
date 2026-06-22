"""Route registry for approved business executors."""

from __future__ import annotations

from collections.abc import Iterable

from business_agents.contracts import BusinessIntent
from business_agents.executors.base_executor import BaseExecutor


class ExecutorRegistry:
    """Resolves one bounded executor for an authorized intent."""

    def __init__(self, executors: Iterable[BaseExecutor] = ()) -> None:
        self._executors: dict[str, BaseExecutor] = {}
        for executor in executors:
            self.register(executor)

    def register(self, executor: BaseExecutor) -> None:
        route = executor.route.strip()
        if not route:
            raise ValueError("executor route is required")
        if route in self._executors:
            raise ValueError(f"executor route already registered: {route}")
        self._executors[route] = executor

    def resolve(self, intent: BusinessIntent) -> BaseExecutor:
        executor = self._executors.get(intent.route)
        if executor is None:
            raise LookupError(f"no executor registered for route: {intent.route}")
        if not executor.supports(intent):
            raise LookupError(
                f"executor does not support action {intent.action!r} "
                f"for route {intent.route!r}"
            )
        return executor

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(sorted(self._executors))
