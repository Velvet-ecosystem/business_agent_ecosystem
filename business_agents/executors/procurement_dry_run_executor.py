"""Dry-run procurement executor for coordinator integration tests."""

from __future__ import annotations

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.procurement_intents import PROCUREMENT_ACTION, PROCUREMENT_ROUTE


class ProcurementDryRunExecutor(BaseExecutor):
    route = PROCUREMENT_ROUTE
    allowed_actions = frozenset({PROCUREMENT_ACTION})

    def execute(
        self,
        intent: BusinessIntent,
        *,
        authorization_id: str,
        authorization_fingerprint: str,
        authorization_issued_at: float,
        authorization_expires_at: float,
    ) -> ExecutorResult:
        artifact_id = str(intent.parameters["artifact_id"])
        return ExecutorResult(
            executor_name="procurement-dry-run",
            status="completed",
            receipt_id=f"dry-run-{artifact_id}",
            output={
                "artifact_id": artifact_id,
                "artifact_digest": str(intent.parameters["artifact_digest"]),
                "handler_id": str(intent.parameters["handler_id"]),
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
                "external_action": False,
            },
        )
