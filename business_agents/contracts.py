"""Strict data contracts shared by agents, Court, and executors."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class RiskLevel(str, Enum):
    """Coarse business-action risk used by policy and approval gates."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalMode(str, Enum):
    """The minimum approval ceremony requested for an intent."""

    POLICY = "policy"
    HUMAN = "human"
    STRONG_HUMAN = "strong-human"


@dataclass(frozen=True)
class BusinessIntent:
    """A bounded proposal submitted for authorization."""

    route: str
    action: str
    subject_id: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    approval_mode: ApprovalMode = ApprovalMode.POLICY

    def __post_init__(self) -> None:
        for name, value in (
            ("route", self.route),
            ("action", self.action),
            ("subject_id", self.subject_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.parameters, Mapping):
            raise ValueError("parameters must be a mapping")
        if not isinstance(self.risk_level, RiskLevel):
            raise ValueError("risk_level must be a RiskLevel")
        if not isinstance(self.approval_mode, ApprovalMode):
            raise ValueError("approval_mode must be an ApprovalMode")
        if self.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} and self.approval_mode is ApprovalMode.POLICY:
            raise ValueError("high-risk intents cannot request policy-only approval")
        if self.risk_level is RiskLevel.CRITICAL and self.approval_mode is not ApprovalMode.STRONG_HUMAN:
            raise ValueError("critical intents require strong human approval")


@dataclass(frozen=True)
class AgentProposal:
    """An agent recommendation with no execution authority."""

    agent_name: str
    intent: BusinessIntent
    rationale: str
    confidence: float
    authority_granted: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.agent_name, str) or not self.agent_name.strip():
            raise ValueError("agent_name must be non-empty")
        if not isinstance(self.intent, BusinessIntent):
            raise ValueError("intent must be a BusinessIntent")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.authority_granted:
            raise ValueError("agent proposals cannot grant authority")


@dataclass(frozen=True)
class AgentHandoff:
    """A structured transfer of bounded context between two agents."""

    source_agent: str
    target_agent: str
    purpose: str
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("source_agent", self.source_agent),
            ("target_agent", self.target_agent),
            ("purpose", self.purpose),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.source_agent.strip() == self.target_agent.strip():
            raise ValueError("an agent cannot hand work to itself")
        if not isinstance(self.context, Mapping):
            raise ValueError("context must be a mapping")


@dataclass(frozen=True)
class ExecutorResult:
    """The bounded outcome returned by an approved executor."""

    executor_name: str
    status: str
    receipt_id: str
    output: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.executor_name, str) or not self.executor_name.strip():
            raise ValueError("executor_name must be non-empty")
        if self.status not in {"completed", "denied", "failed"}:
            raise ValueError("unsupported executor result status")
        if not isinstance(self.receipt_id, str) or not self.receipt_id.strip():
            raise ValueError("receipt_id must be non-empty")
        if not isinstance(self.output, Mapping):
            raise ValueError("output must be a mapping")
