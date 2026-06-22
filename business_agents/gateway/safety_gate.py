"""Safety gate for bounded internal business tasks."""

from __future__ import annotations

from dataclasses import dataclass

from business_agents.contracts import BusinessIntent


@dataclass(frozen=True)
class SafetyDecision:
    passed: bool
    reason: str


class InternalTaskSafetyGate:
    """Allows only small, non-financial internal restock-review tasks."""

    route = "internal-task"
    MAX_QUANTITY = 100

    def evaluate(self, intent: BusinessIntent) -> SafetyDecision:
        if intent.route != self.route:
            return SafetyDecision(False, "unsupported-route")
        if intent.action != "create-restock-review":
            return SafetyDecision(False, "unsupported-action")

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

        return SafetyDecision(True, "safe-internal-task")
