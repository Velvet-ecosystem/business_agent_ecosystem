"""Safety gate for internal booking-confirmation drafts."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class NotificationDraftSafetyGate:
    route = "notification-draft"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "create-booking-confirmation-draft":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.MEDIUM:
            return SafetyDecision(False, "invalid-risk-level")
        if intent.approval_mode is not ApprovalMode.HUMAN:
            return SafetyDecision(False, "human-approval-required")

        allowed = {
            "draft_id",
            "booking_id",
            "job_id",
            "job_status",
            "template",
            "channel",
        }
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "unexpected-notification-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters.get("job_status") != "scheduled":
            return SafetyDecision(False, "job-not-scheduled")
        if intent.parameters.get("template") != "booking-confirmation":
            return SafetyDecision(False, "unsupported-template")
        if intent.parameters.get("channel") != "email":
            return SafetyDecision(False, "unsupported-channel")

        for field in ("draft_id", "booking_id", "job_id"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")

        return SafetyDecision(True, "safe-internal-notification-draft")
