"""Safety gate for invoice finalization."""

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class InvoiceFinalizationSafetyGate:
    route = "invoice-finalization"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "finalize-invoice":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "invoice-finalization-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")
        allowed = {"finalization_id", "invoice_id", "job_id", "approved_by"}
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "invalid-invoice-finalization-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        for field in allowed:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        return SafetyDecision(True, "safe-invoice-finalization")
