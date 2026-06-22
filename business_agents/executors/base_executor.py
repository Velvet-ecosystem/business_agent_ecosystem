"""Base class for approved, bounded business-system executors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from business_agents.contracts import BusinessIntent, ExecutorResult


class BaseExecutor(ABC):
    """Performs one narrow operation after external authorization."""

    route: str
    allowed_actions: frozenset[str]

    def supports(self, intent: BusinessIntent) -> bool:
        return intent.route == self.route and intent.action in self.allowed_actions

    @abstractmethod
    def execute(self, intent: BusinessIntent, *, authorization_id: str) -> ExecutorResult:
        """Execute an already authorized intent and return a receipted result."""
        raise NotImplementedError
