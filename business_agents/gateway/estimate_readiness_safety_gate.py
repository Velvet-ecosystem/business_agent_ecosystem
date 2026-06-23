"""Safety gate for estimate-backed scheduling readiness."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class EstimateReadinessSafetyGate:
    route = "estimate-readiness"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "mark-ready-to-schedule":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.MEDIUM:
            return SafetyDecision(False, "invalid-risk-level")
        if intent.approval_mode is not ApprovalMode.HUMAN:
            return SafetyDecision(False, "human-approval-required")

        allowed = {"job_id", "estimate_id", "current_status", "target_status", "reason"}
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "unexpected-readiness-fields")
        for field in allowed:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        if intent.parameters["job_id"] != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters["current_status"] != "estimating":
            return SafetyDecision(False, "job-not-estimating")
        if intent.parameters["target_status"] != "ready-to-schedule":
            return SafetyDecision(False, "invalid-readiness-target")
        return SafetyDecision(True, "safe-estimate-backed-readiness")
