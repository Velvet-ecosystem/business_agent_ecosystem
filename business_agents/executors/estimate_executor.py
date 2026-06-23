"""Executor for approved internal estimate drafts."""

from __future__ import annotations

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.estimates import EstimateDraft, JsonlEstimateStore, money
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore


class EstimateExecutor(BaseExecutor):
    route = "estimate-draft"
    allowed_actions = frozenset({"create-estimate-draft"})

    def __init__(
        self,
        estimate_store: JsonlEstimateStore,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.estimate_store = estimate_store
        self.receipt_store = receipt_store

    def execute(
        self,
        intent: BusinessIntent,
        *,
        authorization_id: str,
        authorization_fingerprint: str,
        authorization_issued_at: float,
        authorization_expires_at: float,
    ) -> ExecutorResult:
        if not self.supports(intent):
            raise ValueError("unsupported intent")
        if not authorization_id.strip() or not authorization_fingerprint.strip():
            raise ValueError("authorization metadata is required")
        if authorization_expires_at <= authorization_issued_at:
            raise ValueError("authorization lifetime is invalid")

        draft = EstimateDraft(
            estimate_id=str(intent.parameters["estimate_id"]),
            job_id=str(intent.parameters["job_id"]),
            currency=str(intent.parameters["currency"]),
            labour_subtotal=money(intent.parameters["labour_subtotal"]),
            materials_subtotal=money(intent.parameters["materials_subtotal"]),
            contingency_amount=money(intent.parameters["contingency_amount"]),
            margin_amount=money(intent.parameters["margin_amount"]),
            tax_amount=money(intent.parameters["tax_amount"]),
            total=money(intent.parameters["total"]),
            notes=str(intent.parameters.get("notes", "")),
            metadata={
                "job_status": str(intent.parameters["job_status"]),
                "labour_hours": str(intent.parameters["labour_hours"]),
                "labour_rate": str(intent.parameters["labour_rate"]),
                "contingency_rate": str(intent.parameters["contingency_rate"]),
                "margin_rate": str(intent.parameters["margin_rate"]),
                "tax_rate": str(intent.parameters["tax_rate"]),
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        self.estimate_store.create(draft)

        receipt = self.receipt_store.append(
            actor="Estimate Executor",
            decision="completed",
            executor="Estimate Executor",
            subject_id=draft.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "estimate_id": draft.estimate_id,
                "job_id": draft.job_id,
                "currency": draft.currency,
                "total": str(draft.total),
                "draft_only": True,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Estimate Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "estimate_id": draft.estimate_id,
                "job_id": draft.job_id,
                "currency": draft.currency,
                "total": str(draft.total),
                "draft_only": True,
            },
        )
