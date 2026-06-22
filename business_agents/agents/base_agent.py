"""Base class for bounded business agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from business_agents.contracts import AgentProposal


class BaseAgent(ABC):
    """Reasons and proposes. Never performs privileged side effects."""

    def __init__(self, name: str) -> None:
        if not name.strip():
            raise ValueError("agent name must be non-empty")
        self.name = name

    @abstractmethod
    def propose(self, context: Mapping[str, Any]) -> AgentProposal:
        """Return a bounded proposal for Court review."""
        raise NotImplementedError
