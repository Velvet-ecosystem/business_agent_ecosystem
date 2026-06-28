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
    CapabilityDescriptor(
        "invoice-delivery-preparation",
        "strong-human",
        "business_agents.gateway.invoice_delivery_preparation_safety_gate",
        "business_agents.executors.invoice_delivery_preparation_executor",
        False,
    ),
    CapabilityDescriptor(
        "invoice-handoff-confirmation",
        "strong-human",
        "business_agents.gateway.invoice_handoff_confirmation_safety_gate",
        "business_agents.executors.invoice_handoff_confirmation_executor",
        False,
    ),
    CapabilityDescriptor(
        "payment-recording",
        "strong-human",
        "business_agents.gateway.payment_recording_safety_gate",
        "business_agents.executors.reported_amount_recording_executor",
        False,
    ),
    CapabilityDescriptor(
        "customer-account-binding",
        "strong-human",
        "business_agents.gateway.customer_account_binding_safety_gate",
        "business_agents.executors.account_link_executor",
        False,
    ),
    CapabilityDescriptor(
        "change-order",
        "strong-human",
        "business_agents.gateway.change_order_safety_gate",
        "business_agents.executors.amendment_record_executor",
        False,
    ),
    CapabilityDescriptor(
        "job-cost-record",
        "strong-human",
        "business_agents.gateway.job_evidence_safety_gate",
        "business_agents.executors.job_reference_executor",
        False,
    ),
    CapabilityDescriptor(
        "stock-reservation",
        "strong-human",
        "business_agents.gateway.stock_reservation_safety_gate",
        "business_agents.executors.stock_reservation_executor",
        False,
    ),
    CapabilityDescriptor(
        "communication-history",
        "strong-human",
        "business_agents.gateway.communication_history_safety_gate",
        "business_agents.executors.communication_history_executor",
        False,
    ),
    CapabilityDescriptor(
        "report-snapshot",
        "human",
        "business_agents.gateway.report_snapshot_safety_gate",
        "business_agents.executors.report_snapshot_executor",
        False,
    ),
)


def capability_for_route(route: str) -> CapabilityDescriptor | None:
    return next((item for item in CAPABILITIES if item.route == route), None)
