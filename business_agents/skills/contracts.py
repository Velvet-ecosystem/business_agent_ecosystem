"""Contracts shared by bounded skills and their registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from business_agents.contracts import ApprovalMode


class SkillDomain(str, Enum):
    BUSINESS = "business"
    COMMERCE = "commerce"
    PROCUREMENT = "procurement"
    FOUNDRY = "foundry"
    PROTECTIVE = "protective"
    OPERATIONS = "operations"


class SkillEffect(str, Enum):
    READ_ONLY = "read-only"
    STATE_CHANGING = "state-changing"


@dataclass(frozen=True)
class SkillContract:
    """Static declaration of a skill's identity, authority, and behavior."""

    skill_id: str
    version: str
    domain: SkillDomain
    effect: SkillEffect
    approval_mode: ApprovalMode
    input_fields: tuple[str, ...] = ()
    output_fields: tuple[str, ...] = ()
    capability_route: str | None = None
    capability_action: str | None = None
    external_action: bool = False
    receipt_required: bool = False
    artifact_types: tuple[str, ...] = ()
    failure_behavior: str = "fail-closed"
    cancellation_behavior: str = "stop-before-side-effect"
    retry_behavior: str = "manual"

    def __post_init__(self) -> None:
        for name, value in (("skill_id", self.skill_id), ("version", self.version)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.domain, SkillDomain):
            raise ValueError("domain must be a SkillDomain")
        if not isinstance(self.effect, SkillEffect):
            raise ValueError("effect must be a SkillEffect")
        if not isinstance(self.approval_mode, ApprovalMode):
            raise ValueError("approval_mode must be an ApprovalMode")
        for name, values in (
            ("input_fields", self.input_fields),
            ("output_fields", self.output_fields),
            ("artifact_types", self.artifact_types),
        ):
            if not isinstance(values, tuple) or any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{name} must contain non-empty strings")
            if len(values) != len(set(values)):
                raise ValueError(f"{name} cannot contain duplicates")
        has_route = self.capability_route is not None
        has_action = self.capability_action is not None
        if has_route != has_action:
            raise ValueError("capability route and action must be declared together")
        if self.effect is SkillEffect.STATE_CHANGING and not has_route:
            raise ValueError("state-changing skills require a capability route and action")
        if self.external_action and self.effect is not SkillEffect.STATE_CHANGING:
            raise ValueError("external actions must be state-changing")
        if self.external_action and not self.receipt_required:
            raise ValueError("external actions require receipts")
        for name, value in (
            ("failure_behavior", self.failure_behavior),
            ("cancellation_behavior", self.cancellation_behavior),
            ("retry_behavior", self.retry_behavior),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class SkillResult:
    """Result returned by a skill without implying execution authority."""

    skill_id: str
    version: str
    status: str
    output: Mapping[str, Any] = field(default_factory=dict)
    artifacts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (("skill_id", self.skill_id), ("version", self.version)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.status not in {"completed", "cancelled", "failed"}:
            raise ValueError("unsupported skill result status")
        if not isinstance(self.output, Mapping):
            raise ValueError("output must be a mapping")
        if not isinstance(self.artifacts, tuple) or any(
            not isinstance(artifact, str) or not artifact.strip() for artifact in self.artifacts
        ):
            raise ValueError("artifacts must contain non-empty strings")
