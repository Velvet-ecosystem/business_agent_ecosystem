"""Preparation-only wrapper for a booking confirmation draft proposal."""

from __future__ import annotations

from typing import Any, Mapping

from business_agents.agents.notification_draft_agent import NotificationDraftAgent
from business_agents.contracts import ApprovalMode
from business_agents.skills.base import BaseSkill
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect, SkillResult


class PrepareBookingConfirmationSkill(BaseSkill):
    """Prepare a bounded draft proposal without storing or sending a message."""

    contract = SkillContract(
        skill_id="prepare-booking-confirmation",
        version="1.0.0",
        domain=SkillDomain.BUSINESS,
        effect=SkillEffect.READ_ONLY,
        approval_mode=ApprovalMode.POLICY,
        input_fields=("draft_id", "booking_id", "job_id", "job_status"),
        output_fields=("proposal", "send_authority"),
        capability_route="notification-draft",
        capability_action="create-booking-confirmation-draft",
        external_action=False,
        receipt_required=False,
        artifact_types=("agent-proposal",),
        failure_behavior="fail-closed",
        cancellation_behavior="stop-before-draft-storage",
        retry_behavior="safe-preparation-retry",
    )

    def __init__(self, agent: NotificationDraftAgent | None = None) -> None:
        self._agent = agent or NotificationDraftAgent()

    def run(self, inputs: Mapping[str, Any]) -> SkillResult:
        if not isinstance(inputs, Mapping):
            raise ValueError("inputs must be a mapping")
        if set(inputs) != set(self.contract.input_fields):
            raise ValueError("prepare-booking-confirmation requires its exact declared inputs")

        proposal = self._agent.propose({**inputs, "template": "booking-confirmation"})
        intent = proposal.intent
        return SkillResult(
            skill_id=self.contract.skill_id,
            version=self.contract.version,
            status="completed",
            output={
                "proposal": {
                    "agent_name": proposal.agent_name,
                    "route": intent.route,
                    "action": intent.action,
                    "subject_id": intent.subject_id,
                    "parameters": dict(intent.parameters),
                    "risk_level": intent.risk_level.value,
                    "approval_mode": intent.approval_mode.value,
                    "rationale": proposal.rationale,
                    "confidence": proposal.confidence,
                    "authority_granted": proposal.authority_granted,
                },
                "send_authority": False,
            },
            artifacts=("agent-proposal",),
        )
