"""Declarative registry for business capability boundaries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityDescriptor:
    route: str
    approval_mode: str
    gate_module: str
    executor_module: str
    external_action: bool


CAPABILITIES = (
    CapabilityDescriptor("invoice-handoff", "strong-human", "invoice_handoff_safety_gate", "invoice_handoff_executor", False),
    CapabilityDescriptor("payment-reconciliation", "strong-human", "payment_reconciliation_safety_gate", "payment_reconciliation_executor", False),
    CapabilityDescriptor("customer-account", "strong-human", "customer_account_safety_gate", "customer_account_executor", False),
    CapabilityDescriptor("change-order", "strong-human", "change_order_safety_gate", "amendment_record_executor", False),
    CapabilityDescriptor("job-cost-record", "strong-human", "job_evidence_safety_gate", "job_reference_executor", False),
    CapabilityDescriptor("stock-reservation", "strong-human", "stock_reservation_safety_gate", "stock_reservation_executor", False),
    CapabilityDescriptor("communication-history", "strong-human", "communication_history_safety_gate", "communication_history_executor", False),
    CapabilityDescriptor("report-snapshot", "human", "report_snapshot_safety_gate", "report_snapshot_executor", False),
)


def capability_for_route(route: str) -> CapabilityDescriptor | None:
    return next((item for item in CAPABILITIES if item.route == route), None)
