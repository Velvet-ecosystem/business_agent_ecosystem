"""Declarative registry for business capability boundaries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityDescriptor:
    route: str
    action: str
    approval_mode: str
    gate_module: str
    executor_module: str
    external_action: bool


CAPABILITIES = (
    CapabilityDescriptor(
        "invoice-delivery-preparation",
        "prepare-invoice-delivery",
        "strong-human",
        "business_agents.gateway.invoice_delivery_preparation_safety_gate",
        "business_agents.executors.invoice_delivery_preparation_executor",
        False,
    ),
    CapabilityDescriptor(
        "invoice-handoff-confirmation",
        "confirm-invoice-handoff",
        "strong-human",
        "business_agents.gateway.invoice_handoff_confirmation_safety_gate",
        "business_agents.executors.invoice_handoff_confirmation_executor",
        False,
    ),
    CapabilityDescriptor(
        "payment-recording",
        "record-reported-payment",
        "strong-human",
        "business_agents.gateway.payment_recording_safety_gate",
        "business_agents.executors.reported_amount_recording_executor",
        False,
    ),
    CapabilityDescriptor(
        "customer-account-binding",
        "create-and-bind-customer",
        "strong-human",
        "business_agents.gateway.customer_account_binding_safety_gate",
        "business_agents.executors.account_link_executor",
        False,
    ),
    CapabilityDescriptor(
        "change-order",
        "record-change-order",
        "strong-human",
        "business_agents.gateway.change_order_safety_gate",
        "business_agents.executors.amendment_record_executor",
        False,
    ),
    CapabilityDescriptor(
        "job-cost-record",
        "record-job-cost-reference",
        "strong-human",
        "business_agents.gateway.job_evidence_safety_gate",
        "business_agents.executors.job_reference_executor",
        False,
    ),
    CapabilityDescriptor(
        "stock-reservation",
        "record-stock-reservation",
        "strong-human",
        "business_agents.gateway.stock_reservation_safety_gate",
        "business_agents.executors.stock_reservation_executor",
        False,
    ),
    CapabilityDescriptor(
        "communication-history",
        "record-communication-reference",
        "strong-human",
        "business_agents.gateway.communication_history_safety_gate",
        "business_agents.executors.communication_history_executor",
        False,
    ),
    CapabilityDescriptor(
        "report-snapshot",
        "record-report-snapshot",
        "human",
        "business_agents.gateway.report_snapshot_safety_gate",
        "business_agents.executors.report_snapshot_executor",
        False,
    ),
)


def capability_for_route(route: str) -> CapabilityDescriptor | None:
    return next((item for item in CAPABILITIES if item.route == route), None)
