"""Safety gate for real external calendar bookings."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class BookingSafetyGate:
    route = "calendar-booking"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "create-calendar-booking":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "booking-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")

        allowed = {
            "booking_id",
            "job_id",
            "preparation_id",
            "idempotency_key",
            "job_status",
            "title",
            "description",
        }
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "unexpected-booking-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters.get("job_status") != "ready-to-schedule":
            return SafetyDecision(False, "job-not-ready-to-schedule")

        for field in ("booking_id", "job_id", "preparation_id", "idempotency_key", "title"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        return SafetyDecision(True, "safe-calendar-booking-request")
