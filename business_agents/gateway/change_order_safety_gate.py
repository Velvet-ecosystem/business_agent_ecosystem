"""Safety gate for versioned change orders."""

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class ChangeOrderSafetyGate:
    route = "change-order"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "record-change-order":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "change-order-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")
        allowed = {"change_order_id", "job_id", "version", "reason", "scope_delta", "cost_impact_reference", "schedule_impact_reference", "proposed_by"}
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "invalid-change-order-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        for field in allowed:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        try:
            if int(intent.parameters["version"]) < 1:
                return SafetyDecision(False, "invalid-version")
        except ValueError:
            return SafetyDecision(False, "invalid-version")
        return SafetyDecision(True, "safe-change-order")
