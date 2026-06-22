"""Coordinates proposal, safety, Court, routing, execution, and receipts."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import ExecutorResult
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_registry import SafetyGate


class BusinessCoordinator:
    """Runs bounded business-agent proposals through authority and routing."""

    def __init__(
        self,
        *,
        court: CourtPolicy,
        safety_gate: SafetyGate,
        executor_registry: ExecutorRegistry,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.court = court
        self.safety_gate = safety_gate
        self.executor_registry = executor_registry
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
        if (
            not decision.approved
            or decision.authorization_id is None
            or decision.intent_fingerprint is None
            or decision.issued_at is None
            or decision.expires_at is None
        ):
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

        authorization_details = {
            "authorization_id": decision.authorization_id,
            "authorization_fingerprint": decision.intent_fingerprint,
            "authorization_issued_at": decision.issued_at,
            "authorization_expires_at": decision.expires_at,
        }

        try:
            executor = self.executor_registry.resolve(proposal.intent)
        except LookupError as exc:
            self.receipt_store.append(
                actor="Executor Registry",
                decision="denied",
                executor=None,
                subject_id=proposal.intent.subject_id,
                details={
                    "reason": "executor-not-available",
                    "route": proposal.intent.route,
                    "action": proposal.intent.action,
                    **authorization_details,
                    "error": str(exc),
                },
            )
            raise PermissionError("executor-not-available") from exc

        if not self.court.consume_authorization(
            decision.authorization_id,
            proposal.intent,
        ):
            self.receipt_store.append(
                actor="Court",
                decision="denied",
                executor=None,
                subject_id=proposal.intent.subject_id,
                details={
                    "reason": "authorization-invalid-or-expired",
                    "route": proposal.intent.route,
                    "action": proposal.intent.action,
                    **authorization_details,
                },
            )
            raise PermissionError("authorization-invalid-or-expired")

        return executor.execute(
            proposal.intent,
            authorization_id=decision.authorization_id,
            authorization_fingerprint=decision.intent_fingerprint,
            authorization_issued_at=decision.issued_at,
            authorization_expires_at=decision.expires_at,
        )
