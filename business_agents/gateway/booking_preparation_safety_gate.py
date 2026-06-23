"""Safety gate for exact-window booking preparation."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class BookingPreparationSafetyGate:
    route = "booking-preparation"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "prepare-selected-window":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.MEDIUM:
            return SafetyDecision(False, "invalid-risk-level")
        if intent.approval_mode is not ApprovalMode.HUMAN:
            return SafetyDecision(False, "human-approval-required")

        allowed = {
            "preparation_id",
            "proposal_id",
            "job_id",
            "job_status",
            "selected_index",
            "notes",
        }
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "unexpected-booking-preparation-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters.get("job_status") != "ready-to-schedule":
            return SafetyDecision(False, "job-not-ready-to-schedule")

        for field in ("preparation_id", "proposal_id", "job_id"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        selected_index = intent.parameters.get("selected_index")
        if not isinstance(selected_index, int) or isinstance(selected_index, bool):
            return SafetyDecision(False, "invalid-selected-index")
        if selected_index < 0:
            return SafetyDecision(False, "invalid-selected-index")

        return SafetyDecision(True, "safe-booking-preparation")
