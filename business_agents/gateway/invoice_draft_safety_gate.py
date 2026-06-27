"""Safety gate for local invoice drafting."""

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class InvoiceDraftSafetyGate:
    route = "invoice-draft"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "create-invoice-draft":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "invoice-draft-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")
        allowed = {"invoice_id", "job_id", "job_status", "evidence_id", "currency", "subtotal", "tax_amount", "total", "notes"}
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "invalid-invoice-draft-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters.get("job_status") != "completed":
            return SafetyDecision(False, "job-must-be-completed")
        for field in ("invoice_id", "job_id", "evidence_id", "currency", "subtotal", "tax_amount", "total"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        return SafetyDecision(True, "safe-invoice-draft")
