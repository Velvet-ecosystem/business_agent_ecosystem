"""Read-only summary of local invoice drafts."""

from typing import Any, Mapping

from business_agents.contracts import ApprovalMode
from business_agents.invoice_draft_store import JsonlInvoiceDraftStore
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class InvoiceDraftSummarySkill(BaseSkill):
    contract = SkillContract(
        skill_id="invoice-draft-summary",
        version="1.0.0",
        domain=SkillDomain.BUSINESS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        output_fields=("scope", "draft_count", "drafts"),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-immediately",
        retry_behavior="safe-read-retry",
    )

    def __init__(self, invoice_store: JsonlInvoiceDraftStore) -> None:
        self._invoice_store = invoice_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if inputs:
            raise ValueError("invoice-draft-summary accepts no inputs")
        drafts = self._invoice_store.list_current()
        rows = tuple(
            {
                "invoice_id": draft.invoice_id,
                "job_id": draft.job_id,
                "currency": draft.currency,
                "total": str(draft.total),
            }
            for draft in drafts
        )
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "scope": "invoice-drafts-only",
                "draft_count": len(rows),
                "drafts": rows,
            },
        )
