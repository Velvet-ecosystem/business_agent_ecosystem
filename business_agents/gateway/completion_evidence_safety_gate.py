"""Safety gate for durable completion evidence."""

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class CompletionEvidenceSafetyGate:
    route = "completion-evidence"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "record-completion-evidence":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.HIGH:
            return SafetyDecision(False, "completion-evidence-risk-too-low")
        if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
            return SafetyDecision(False, "strong-human-approval-required")

        required = {"evidence_id", "job_id", "job_status", "completed_by", "summary", "checklist", "artifact_refs", "customer_acknowledged"}
        if set(intent.parameters) != required:
            return SafetyDecision(False, "invalid-completion-evidence-fields")
        if intent.parameters["job_id"] != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters["job_status"] != "in-progress":
            return SafetyDecision(False, "job-must-be-in-progress")
        for field in ("evidence_id", "job_id", "completed_by", "summary"):
            value = intent.parameters[field]
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        checklist = intent.parameters["checklist"]
        artifacts = intent.parameters["artifact_refs"]
        if not isinstance(checklist, tuple) or not checklist or any(not isinstance(item, str) or not item.strip() for item in checklist):
            return SafetyDecision(False, "invalid-checklist")
        if not isinstance(artifacts, tuple) or any(not isinstance(item, str) or not item.strip() for item in artifacts):
            return SafetyDecision(False, "invalid-artifact-references")
        if not isinstance(intent.parameters["customer_acknowledged"], bool):
            return SafetyDecision(False, "invalid-customer-acknowledged")
        return SafetyDecision(True, "safe-completion-evidence")
