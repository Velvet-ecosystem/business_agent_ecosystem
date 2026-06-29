"""Base interface for bounded skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, Any

from business_agents.skills.contracts import SkillContract, SkillResult


class BaseSkill(ABC):
    """A discoverable skill with a static contract and bounded execution path."""

    contract: SkillContract

    @abstractmethod
    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        """Run the skill against validated inputs."""
        raise NotImplementedError
