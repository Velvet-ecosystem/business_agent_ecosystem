"""Safety gate for bounded internal business tasks."""

from __future__ import annotations

from dataclasses import dataclass

from business_agents.contracts import BusinessIntent


@dataclass(frozen=True)
class SafetyDecision:
    passed: bool
    reason: str


class InternalTaskSafetyGate:
    """Allows only small, non-financial internal review tasks."""

    route = "internal-task"
    MAX_QUANTITY = 100

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")

        if intent.action == "create-restock-review":
            return self._evaluate_restock(intent)
        if intent.action == "create-intake-review":
            return self._evaluate_intake(intent)
        return SafetyDecision(False, "unsupported-action")

    def _evaluate_restock(self, intent: BusinessIntent) -> SafetyDecision:
        sku = intent.parameters.get("sku")
        if not isinstance(sku, str) or not sku.strip():
            return SafetyDecision(False, "invalid-sku")

        quantity = intent.parameters.get("suggested_quantity")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            return SafetyDecision(False, "invalid-quantity")
        if quantity > self.MAX_QUANTITY:
            return SafetyDecision(False, "quantity-exceeds-limit")

        forbidden = {"price", "payment", "vendor_login", "purchase_order"}
        if forbidden.intersection(intent.parameters):
            return SafetyDecision(False, "financial-fields-forbidden")

        return SafetyDecision(True, "safe-internal-restock-task")

    def _evaluate_intake(self, intent: BusinessIntent) -> SafetyDecision:
        required = ("customer_name", "contact", "request", "source")
        for field in required:
            value = intent.parameters.get(field)
            if not isinstance(value, str) or not value.strip():
                return SafetyDecision(False, f"invalid-{field.replace('_', '-')}")

        if len(str(intent.parameters["request"])) > 2000:
            return SafetyDecision(False, "request-too-long")

        forbidden = {
            "send_message",
            "book_appointment",
            "quote_total",
            "payment",
            "card_number",
            "bank_account",
        }
        if forbidden.intersection(intent.parameters):
            return SafetyDecision(False, "external-or-financial-fields-forbidden")

        return SafetyDecision(True, "safe-internal-intake-task")
