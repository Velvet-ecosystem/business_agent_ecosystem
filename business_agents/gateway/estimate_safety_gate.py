"""Safety gate for internal estimate drafts."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class EstimateDraftSafetyGate:
    """Allows only human-approved, internal, bounded estimate drafts."""

    route = "estimate-draft"
    MAX_TOTAL = Decimal("1000000.00")

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "create-estimate-draft":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.MEDIUM:
            return SafetyDecision(False, "invalid-risk-level")
        if intent.approval_mode is not ApprovalMode.HUMAN:
            return SafetyDecision(False, "human-approval-required")
        if intent.parameters.get("job_status") != "estimating":
            return SafetyDecision(False, "job-not-estimating")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")

        required = (
            "estimate_id",
            "job_id",
            "currency",
            "labour_subtotal",
            "materials_subtotal",
            "contingency_amount",
            "margin_amount",
            "tax_amount",
            "total",
        )
        for field in required:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")

        try:
            components = [
                Decimal(str(intent.parameters[name]))
                for name in (
                    "labour_subtotal",
                    "materials_subtotal",
                    "contingency_amount",
                    "margin_amount",
                    "tax_amount",
                )
            ]
            total = Decimal(str(intent.parameters["total"]))
        except (InvalidOperation, ValueError):
            return SafetyDecision(False, "invalid-money-value")
        if any(not value.is_finite() or value < 0 for value in [*components, total]):
            return SafetyDecision(False, "invalid-money-value")
        if sum(components) != total:
            return SafetyDecision(False, "estimate-total-mismatch")
        if total > self.MAX_TOTAL:
            return SafetyDecision(False, "estimate-total-exceeds-limit")

        forbidden = {
            "send_quote",
            "customer_message",
            "payment_link",
            "contract_signature",
            "scheduled_at",
            "approved_by_customer",
        }
        if forbidden.intersection(intent.parameters):
            return SafetyDecision(False, "external-action-fields-forbidden")

        return SafetyDecision(True, "safe-internal-estimate-draft")
