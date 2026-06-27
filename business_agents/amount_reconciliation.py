"""Pure arithmetic for comparing recorded amounts with a target total."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AmountReconciliation:
    recorded_total: Decimal
    remaining: Decimal
    state: str


def reconcile(target_total: Decimal, existing_total: Decimal, new_amount: Decimal) -> AmountReconciliation:
    recorded_total = existing_total + new_amount
    if recorded_total > target_total:
        raise ValueError("recorded total exceeds target total")
    remaining = target_total - recorded_total
    state = "complete" if remaining == 0 else "partial"
    return AmountReconciliation(recorded_total, remaining, state)
