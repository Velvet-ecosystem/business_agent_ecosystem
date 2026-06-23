"""Safety gate for external notification delivery."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class NotificationDeliverySafetyGate:
    route = "notification-delivery"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "deliver-notification-draft":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "delivery-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")
        allowed = {"delivery_id", "draft_id", "job_id", "idempotency_key", "job_status"}
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "unexpected-delivery-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters.get("job_status") != "scheduled":
            return SafetyDecision(False, "job-not-scheduled")
        for field in ("delivery_id", "draft_id", "job_id", "idempotency_key"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        return SafetyDecision(True, "safe-notification-delivery")
