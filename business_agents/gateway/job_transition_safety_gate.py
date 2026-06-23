"""Safety gate for explicit job lifecycle transitions."""

from __future__ import annotations

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision
from business_agents.jobs import JobRecord, JobStatus


class JobTransitionSafetyGate:
    route = "job-transition"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "transition-job":
            return SafetyDecision(False, "unsupported-action")

        for field in ("job_id", "current_status", "target_status", "reason"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")
        if intent.parameters["job_id"] != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")

        try:
            current = JobStatus(str(intent.parameters["current_status"]))
            target = JobStatus(str(intent.parameters["target_status"]))
        except ValueError:
            return SafetyDecision(False, "unsupported-job-status")

        terminal = target in {JobStatus.COMPLETED, JobStatus.CANCELLED}
        if terminal:
            if intent.risk_level is not RiskLevel.HIGH:
                return SafetyDecision(False, "terminal-transition-risk-too-low")
            if intent.approval_mode is not ApprovalMode.STRONG_HUMAN:
                return SafetyDecision(False, "strong-human-approval-required")
        else:
            if intent.risk_level is not RiskLevel.MEDIUM:
                return SafetyDecision(False, "invalid-risk-level")
            if intent.approval_mode is not ApprovalMode.HUMAN:
                return SafetyDecision(False, "human-approval-required")

        probe = JobRecord(
            job_id=intent.subject_id,
            customer_name="validation",
            contact="validation",
            request="validation",
            source="validation",
            status=current,
        )
        try:
            probe.transition(target)
        except ValueError:
            return SafetyDecision(False, "invalid-job-transition")

        allowed = {"job_id", "current_status", "target_status", "reason"}
        if set(intent.parameters) - allowed:
            return SafetyDecision(False, "unexpected-transition-fields")

        return SafetyDecision(True, "safe-job-transition")
