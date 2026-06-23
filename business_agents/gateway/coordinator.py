"""Coordinate proposal, safety, Court authorization, execution, and receipts."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.base_agent import BaseAgent
from business_agents.contracts import ExecutorResult
from business_agents.executors.registry import ExecutorRegistry
from business_agents.gateway.authority import CourtPolicy
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.gateway.safety_registry import SafetyGate


class BusinessCoordinator:
    def __init__(self, *, court: CourtPolicy, safety_gate: SafetyGate,
                 executor_registry: ExecutorRegistry,
                 receipt_store: JsonlReceiptStore) -> None:
        self.court = court
        self.safety_gate = safety_gate
        self.executor_registry = executor_registry
        self.receipt_store = receipt_store

    def run(self, agent: BaseAgent, context: Mapping[str, Any], *,
            identity_verified: bool) -> ExecutorResult:
        principal_id = self._text(context, "_principal_id")
        session_id = self._text(context, "_principal_session_id")
        if (principal_id is None) != (session_id is None):
            raise PermissionError("incomplete-principal-binding")

        proposal = agent.propose(context)
        safety = self.safety_gate.evaluate(proposal.intent)
        decision = self.court.evaluate(
            proposal,
            identity_verified=identity_verified,
            safety_passed=safety.passed,
            principal_id=principal_id,
            session_id=session_id,
        )
        actor = {
            "principal_id": principal_id,
            "principal_session_id": session_id,
            "principal_display_name": self._text(context, "_principal_display_name"),
            "principal_role": self._text(context, "_principal_role"),
            "principal_presence_level": self._text(context, "_principal_presence_level"),
        }
        if not all((decision.approved, decision.authorization_id,
                    decision.intent_fingerprint, decision.issued_at,
                    decision.expires_at)):
            self.receipt_store.append(
                actor="Court", decision="denied", executor=None,
                subject_id=proposal.intent.subject_id,
                details={"agent_name": proposal.agent_name,
                         "reason": decision.reason,
                         "identity_verified": identity_verified,
                         "safety_passed": safety.passed,
                         "safety_reason": safety.reason,
                         "route": proposal.intent.route,
                         "action": proposal.intent.action, **actor},
            )
            raise PermissionError(decision.reason)

        auth = {
            "authorization_id": decision.authorization_id,
            "authorization_fingerprint": decision.intent_fingerprint,
            "authorization_issued_at": decision.issued_at,
            "authorization_expires_at": decision.expires_at,
            **actor,
        }
        if principal_id is not None:
            self.receipt_store.append(
                actor="Court", decision="authorized", executor=None,
                subject_id=proposal.intent.subject_id,
                details={"agent_name": proposal.agent_name,
                         "route": proposal.intent.route,
                         "action": proposal.intent.action, **auth},
            )
        try:
            executor = self.executor_registry.resolve(proposal.intent)
        except LookupError as exc:
            self.receipt_store.append(
                actor="Executor Registry", decision="denied", executor=None,
                subject_id=proposal.intent.subject_id,
                details={"reason": "executor-not-available",
                         "route": proposal.intent.route,
                         "action": proposal.intent.action,
                         "error": str(exc), **auth},
            )
            raise PermissionError("executor-not-available") from exc

        if not self.court.consume_authorization(
            decision.authorization_id, proposal.intent,
            principal_id=principal_id, session_id=session_id,
        ):
            self.receipt_store.append(
                actor="Court", decision="denied", executor=None,
                subject_id=proposal.intent.subject_id,
                details={"reason": "authorization-invalid-or-expired",
                         "route": proposal.intent.route,
                         "action": proposal.intent.action, **auth},
            )
            raise PermissionError("authorization-invalid-or-expired")

        return executor.execute(
            proposal.intent,
            authorization_id=decision.authorization_id,
            authorization_fingerprint=decision.intent_fingerprint,
            authorization_issued_at=decision.issued_at,
            authorization_expires_at=decision.expires_at,
        )

    @staticmethod
    def _text(context: Mapping[str, Any], key: str) -> str | None:
        value = context.get(key)
        if value is None:
            return None
        text = str(value).strip()
        return text or None
