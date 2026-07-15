"""Read-only verification for procurement dry-run evidence."""

from __future__ import annotations

from dataclasses import dataclass

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.gateway.receipt_store import JsonlReceiptStore, Receipt
from business_agents.procurement_intents import PROCUREMENT_ACTION, PROCUREMENT_ROUTE


@dataclass(frozen=True)
class ProcurementVerification:
    passed: bool
    reason: str


def verify_procurement_dry_run(
    *,
    intent: BusinessIntent,
    result: ExecutorResult,
    receipt: Receipt,
    receipt_store: JsonlReceiptStore,
) -> ProcurementVerification:
    if intent.route != PROCUREMENT_ROUTE or intent.action != PROCUREMENT_ACTION:
        return ProcurementVerification(False, "unsupported-intent")
    if result.executor_name != "procurement-dry-run":
        return ProcurementVerification(False, "unexpected-executor")
    if result.status != "completed":
        return ProcurementVerification(False, "unexpected-result-status")
    if result.output.get("external_action") is not False:
        return ProcurementVerification(False, "external-action-flag-not-false")
    if not receipt_store.verify(receipt):
        return ProcurementVerification(False, "invalid-receipt")
    if receipt.actor != "Court" or receipt.decision != "authorized":
        return ProcurementVerification(False, "unexpected-receipt-decision")
    if receipt.executor is not None:
        return ProcurementVerification(False, "unexpected-receipt-executor")

    artifact_id = intent.parameters.get("artifact_id")
    artifact_digest = intent.parameters.get("artifact_digest")
    handler_id = intent.parameters.get("handler_id")
    if intent.subject_id != artifact_id:
        return ProcurementVerification(False, "subject-artifact-mismatch")
    if result.output.get("artifact_id") != artifact_id:
        return ProcurementVerification(False, "result-artifact-mismatch")
    if result.output.get("artifact_digest") != artifact_digest:
        return ProcurementVerification(False, "result-digest-mismatch")
    if result.output.get("handler_id") != handler_id:
        return ProcurementVerification(False, "result-handler-mismatch")
    if receipt.subject_id != artifact_id:
        return ProcurementVerification(False, "receipt-artifact-mismatch")
    if receipt.details.get("route") != intent.route:
        return ProcurementVerification(False, "receipt-route-mismatch")
    if receipt.details.get("action") != intent.action:
        return ProcurementVerification(False, "receipt-action-mismatch")
    if receipt.details.get("authorization_id") != result.output.get("authorization_id"):
        return ProcurementVerification(False, "authorization-id-mismatch")
    if receipt.details.get("authorization_fingerprint") != result.output.get(
        "authorization_fingerprint"
    ):
        return ProcurementVerification(False, "authorization-fingerprint-mismatch")
    return ProcurementVerification(True, "verified-procurement-dry-run")
