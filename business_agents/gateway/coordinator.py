"""Coordinates proposal, safety, Court, execution, and receipts."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_gate import InternalTaskSafetyGate


class BusinessCoordinator:
    """Routes authorized intents to one matching bounded executor."""

    def __init__(
        self,
        *,
        court: CourtPolicy,
        safety_gate: InternalTaskSafetyGate,
        executors: Sequence[BaseExecutor],
        receipt_store: JsonlReceiptStore,
    ) -> None:
        if not executors:
            raise ValueError("at least one executor is required")
        self.court = court
        self.safety_gate = safety_gate
        self.executors = tuple(executors)
        self.receipt_store = receipt_store

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
            self.receipt_store.append(
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

        executor = self._select_executor(proposal.intent)
        return executor.execute(
            proposal.intent,
            authorization_id=decision.authorization_id,
        )

    def _select_executor(self, intent: BusinessIntent) -> BaseExecutor:
        matches = [executor for executor in self.executors if executor.supports(intent)]
        if not matches:
            self.receipt_store.append(
                actor="Business Coordinator",
                decision="denied",
                executor=None,
                subject_id=intent.subject_id,
                details={
                    "reason": "no-matching-executor",
                    "route": intent.route,
                    "action": intent.action,
                },
            )
            raise LookupError("no-matching-executor")
        if len(matches) > 1:
            self.receipt_store.append(
                actor="Business Coordinator",
                decision="denied",
                executor=None,
                subject_id=intent.subject_id,
                details={
                    "reason": "ambiguous-executor-route",
                    "route": intent.route,
                    "action": intent.action,
                    "matches": [type(executor).__name__ for executor in matches],
                },
            )
            raise RuntimeError("ambiguous-executor-route")
        return matches[0]
