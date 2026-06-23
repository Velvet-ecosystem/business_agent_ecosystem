"""Safety gate for explicit work-start ceremonies."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class WorkStartSafetyGate:
    route = "work-start"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "start-work":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "work-start-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")

        allowed = {
            "start_id",
            "job_id",
            "booking_id",
            "started_by",
            "reason",
            "job_status",
        }
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "unexpected-work-start-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters.get("job_status") != "scheduled":
            return SafetyDecision(False, "job-not-scheduled")

        for field in ("start_id", "job_id", "booking_id", "started_by", "reason"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")

        return SafetyDecision(True, "safe-work-start")
