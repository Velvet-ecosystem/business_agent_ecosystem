"""Safety gate for durable internal job records."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class JobRecordSafetyGate:
    """Allows only human-approved creation of internal job records."""

    route = "job-record"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "create-job":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.MEDIUM:
            return SafetyDecision(False, "invalid-risk-level")
        if intent.approval_mode is not ApprovalMode.HUMAN:
            return SafetyDecision(False, "human-approval-required")

        required = (
            "job_id",
            "customer_name",
            "contact",
            "request",
            "source",
            "intake_task_id",
        )
        for field in required:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")

        if intent.parameters["job_id"] != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")

        forbidden = {
            "quote_total",
            "scheduled_at",
            "contract_signature",
            "payment",
            "send_message",
        }
        if forbidden.intersection(intent.parameters):
            return SafetyDecision(False, "commercial-action-fields-forbidden")

        return SafetyDecision(True, "safe-job-record-creation")
