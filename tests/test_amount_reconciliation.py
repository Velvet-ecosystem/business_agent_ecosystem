from decimal import Decimal

import pytest

from business_agents.amount_reconciliation import reconcile


def test_reconcile_partial_amount() -> None:
    result = reconcile(Decimal("105.00"), Decimal("0.00"), Decimal("40.00"))
    assert result.recorded_total == Decimal("40.00")
    assert result.remaining == Decimal("65.00")
    assert result.state == "partial"


def test_reconcile_complete_amount() -> None:
    result = reconcile(Decimal("105.00"), Decimal("40.00"), Decimal("65.00"))
    assert result.recorded_total == Decimal("105.00")
    assert result.remaining == Decimal("0.00")
    assert result.state == "complete"


def test_reconcile_rejects_excess() -> None:
    with pytest.raises(ValueError, match="recorded total exceeds target total"):
        reconcile(Decimal("105.00"), Decimal("40.00"), Decimal("66.00"))
