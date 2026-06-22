"""Safety gate for bounded internal operations notes."""

from __future__ import annotations

from business_agents.contracts import BusinessIntent
from business_agents.gateway.safety_gate import SafetyDecision


class InternalNoteSafetyGate:
    """Allows short local-only notes with no external side effects."""

    route = "internal-note"
    MAX_TITLE_LENGTH = 120
    MAX_BODY_LENGTH = 2000

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "record-operations-note":
            return SafetyDecision(False, "unsupported-action")

        title = intent.parameters.get("title")
        body = intent.parameters.get("body")
        if not isinstance(title, str) or not title.strip():
            return SafetyDecision(False, "invalid-title")
        if len(title.strip()) > self.MAX_TITLE_LENGTH:
            return SafetyDecision(False, "title-too-long")
        if not isinstance(body, str) or not body.strip():
            return SafetyDecision(False, "invalid-body")
        if len(body.strip()) > self.MAX_BODY_LENGTH:
            return SafetyDecision(False, "body-too-long")

        forbidden = {"recipient", "email", "webhook", "payment", "purchase_order"}
        if forbidden.intersection(intent.parameters):
            return SafetyDecision(False, "external-fields-forbidden")

        return SafetyDecision(True, "safe-internal-note")
