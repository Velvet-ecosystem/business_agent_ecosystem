"""Safety gate for canonical procurement intents."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision
from business_agents.procurement_intents import PROCUREMENT_ACTION, PROCUREMENT_ROUTE


class ProcurementSafetyGate:
    route = PROCUREMENT_ROUTE

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != PROCUREMENT_ACTION:
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "invalid-risk-level")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "invalid-approval-mode")

        required = (
            "artifact_id",
            "artifact_digest",
            "handler_id",
            "approval_request_id",
            "decision_id",
            "lineage_route",
            "lineage_action",
            "lineage_subject_id",
        )
        for name in required:
            value = intent.parameters.get(name)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{name.replace('_', '-')}")

        artifact_id = str(intent.parameters["artifact_id"])
        artifact_digest = str(intent.parameters["artifact_digest"])
        if intent.subject_id != artifact_id:
            return SafetyDecision(False, "subject-artifact-mismatch")
        if len(artifact_digest) != 64 or any(
            character not in "0123456789abcdef" for character in artifact_digest
        ):
            return SafetyDecision(False, "invalid-artifact-digest")
        if intent.parameters["lineage_route"] != PROCUREMENT_ROUTE:
            return SafetyDecision(False, "lineage-route-mismatch")
        if intent.parameters["lineage_action"] != PROCUREMENT_ACTION:
            return SafetyDecision(False, "lineage-action-mismatch")
        if intent.parameters["lineage_subject_id"] != artifact_id:
            return SafetyDecision(False, "lineage-subject-mismatch")
        return SafetyDecision(True, "safe-procurement-intent")
