"""Safety gate for invoice handoff confirmation."""

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class InvoiceHandoffConfirmationSafetyGate:
    route = "invoice-handoff-confirmation"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "confirm-invoice-handoff":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "invoice-handoff-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")
        allowed = {"confirmation_id", "preparation_id", "invoice_id", "job_id", "channel_reference", "recipient_reference", "confirmed_by"}
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "invalid-invoice-handoff-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        for field in allowed:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        return SafetyDecision(True, "safe-invoice-handoff-confirmation")
