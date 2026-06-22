"""Coordinates proposal, safety, Court, execution, and receipts."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import ExecutorResult
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.safety_gate import InternalTaskSafetyGate


class BusinessCoordinator:
    """Runs one bounded business-agent vertical slice."""

    def __init__(
        self,
        *,
        court: CourtPolicy,
        safety_gate: InternalTaskSafetyGate,
        task_executor: TaskExecutor,
    ) -> None:
        self.court = court
        self.safety_gate = safety_gate
        self.task_executor = task_executor

    def run(
        self,
        agent: BaseAgent,
        context: Mapping[str, Any],
        *,
        identity_verified: bool,
    ) -> ExecutorResult:
        proposal = agent.propose(context)
        safety = self.safety_gate.evaluate(proposal.intent)
        decision = self.court.evaluate(
            proposal,
            identity_verified=identity_verified,
            safety_passed=safety.passed,
        )
        if not decision.approved or decision.authorization_id is None:
            self.task_executor.receipt_store.append(
                actor="Court",
                decision="denied",
                executor=None,
                subject_id=proposal.intent.subject_id,
                details={
                    "agent_name": proposal.agent_name,
                    "reason": decision.reason,
                    "identity_verified": identity_verified,
                    "safety_passed": safety.passed,
                    "safety_reason": safety.reason,
                    "route": proposal.intent.route,
                    "action": proposal.intent.action,
                },
            )
            raise PermissionError(decision.reason)
        return self.task_executor.execute(
            proposal.intent,
            authorization_id=decision.authorization_id,
        )
