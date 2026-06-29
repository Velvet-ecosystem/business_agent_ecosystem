"""Deterministic registry for bounded skills."""

from __future__ import annotations

from collections.abc import Iterable

from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract


class SkillRegistry:
    def __init__(self, skills: Iterable[BaseSkill] = ()) -> None:
        self._skills: dict[str, BaseSkill] = {}
        for skill in skills:
            self.register(skill)

    def register(self, skill: BaseSkill) -> None:
        if not isinstance(skill, BaseSkill):
            raise TypeError("skill must be a BaseSkill")
        skill_id = skill.contract.skill_id
        if skill_id in self._skills:
            raise ValueError(f"skill already registered: {skill_id}")
        self._skills[skill_id] = skill

    def get(self, skill_id: str) -> BaseSkill:
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise ValueError("skill_id must be a non-empty string")
        if skill_id not in self._skills:
            raise KeyError(f"skill not registered: {skill_id}")
        return self._skills[skill_id]

    def list_contracts(self) -> tuple[SkillContract, ...]:
        return tuple(self._skills[key].contract for key in sorted(self._skills))
