"""Strict data contracts shared by agents, Court, and executors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class BusinessIntent:
    """A bounded proposal submitted for authorization."""

    route: str
    action: str
    subject_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("route", self.route),
            ("action", self.action),
            ("subject_id", self.subject_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class AgentProposal:
    """An agent recommendation with no execution authority."""

    agent_name: str
    intent: BusinessIntent
    rationale: str
    confidence: float
    authority_granted: bool = False

    def __post_init__(self) -> None:
        if not self.agent_name.strip():
            raise ValueError("agent_name must be non-empty")
        if not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.authority_granted:
            raise ValueError("agent proposals cannot grant authority")


@dataclass(frozen=True)
class ExecutorResult:
    """The bounded outcome returned by an approved executor."""

    executor_name: str
    status: str
    receipt_id: str
    output: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.executor_name.strip():
            raise ValueError("executor_name must be non-empty")
        if self.status not in {"completed", "denied", "failed"}:
            raise ValueError("unsupported executor result status")
        if not self.receipt_id.strip():
            raise ValueError("receipt_id must be non-empty")
