"""Read-only customer communication history summary."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from business_agents.communication_records import CommunicationRecordStore
from business_agents.contracts import ApprovalMode
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class CustomerHistorySummarySkill(BaseSkill):
    contract = SkillContract(
        skill_id="customer-history-summary",
        version="1.0.0",
        domain=SkillDomain.BUSINESS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=("customer_reference",),
        output_fields=("customer_reference", "total_records", "channel_counts", "direction_counts", "job_ids", "records"),
        external_action=False,
        receipt_required=False,
        failure_behavior="fail-closed",
        cancellation_behavior="stop-immediately",
        retry_behavior="safe-read-retry",
    )

    def __init__(self, communication_store: CommunicationRecordStore) -> None:
        self._communication_store = communication_store

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if set(inputs) != {"customer_reference"}:
            raise ValueError("customer-history-summary requires only customer_reference")
        customer_reference = inputs["customer_reference"]
        if not isinstance(customer_reference, str) or not customer_reference.strip():
            raise ValueError("customer_reference must be a non-empty string")

        records = self._communication_store.list_for_customer(customer_reference)
        ordered = tuple(sorted(records, key=lambda record: record.record_id))
        channel_counts = Counter(record.channel for record in ordered)
        direction_counts = Counter(record.direction for record in ordered)
        summaries = tuple(
            {
                "record_id": record.record_id,
                "job_id": record.job_id,
                "channel": record.channel,
                "direction": record.direction,
            }
            for record in ordered
        )
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "customer_reference": customer_reference,
                "total_records": len(ordered),
                "channel_counts": dict(sorted(channel_counts.items())),
                "direction_counts": dict(sorted(direction_counts.items())),
                "job_ids": tuple(sorted({record.job_id for record in ordered})),
                "records": summaries,
            },
        )
