"""Safety gate for derived report snapshots."""

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class ReportSnapshotSafetyGate:
    route = "report-snapshot"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "record-report-snapshot":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.MEDIUM:
            return SafetyDecision(False, "invalid-report-risk")
        if intent.approval_mode is not ApprovalMode.HUMAN:
            return SafetyDecision(False, "human-approval-required")
        allowed = {
            "report_id",
            "report_type",
            "scope_reference",
            "source_reference",
            "generated_by",
            "generated_at_reference",
        }
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "invalid-report-fields")
        if intent.parameters.get("scope_reference") != intent.subject_id:
            return SafetyDecision(False, "scope-subject-mismatch")
        for field in allowed:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        return SafetyDecision(True, "safe-report-snapshot")
