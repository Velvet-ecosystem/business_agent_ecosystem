"""Safety gate for internal schedule proposals."""

from __future__ import annotations

from datetime import datetime

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.safety_gate import SafetyDecision


class ScheduleProposalSafetyGate:
    route = "schedule-proposal"

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "create-schedule-proposal":
            return SafetyDecision(False, "unsupported-action")
        if intent.risk_level is not RiskLevel.MEDIUM:
            return SafetyDecision(False, "invalid-risk-level")
        if intent.approval_mode is not ApprovalMode.HUMAN:
            return SafetyDecision(False, "human-approval-required")

        allowed = {"proposal_id", "job_id", "job_status", "timezone", "windows", "notes"}
        if set(intent.parameters) != allowed:
            return SafetyDecision(False, "unexpected-schedule-fields")
        if intent.parameters.get("job_id") != intent.subject_id:
            return SafetyDecision(False, "job-id-subject-mismatch")
        if intent.parameters.get("job_status") != "ready-to-schedule":
            return SafetyDecision(False, "job-not-ready-to-schedule")

        for field in ("proposal_id", "job_id", "timezone"):
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")

        windows = intent.parameters.get("windows")
        if not isinstance(windows, (list, tuple)) or not 1 <= len(windows) <= 10:
            return SafetyDecision(False, "invalid-window-count")
        previous_end: datetime | None = None
        for item in windows:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                return SafetyDecision(False, "invalid-window-shape")
            try:
                start = datetime.fromisoformat(str(item[0]))
                end = datetime.fromisoformat(str(item[1]))
            except ValueError:
                return SafetyDecision(False, "invalid-window-time")
            if start.tzinfo is None or end.tzinfo is None or end <= start:
                return SafetyDecision(False, "invalid-window-time")
            if previous_end is not None and start < previous_end:
                return SafetyDecision(False, "windows-overlap-or-unsorted")
            previous_end = end

        return SafetyDecision(True, "safe-internal-schedule-proposal")
