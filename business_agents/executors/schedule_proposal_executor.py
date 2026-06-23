"""Executor for approved internal schedule proposals."""

from __future__ import annotations

from datetime import datetime

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.jobs import JobStatus, JsonlJobStore
from business_agents.schedules import JsonlScheduleStore, ScheduleProposal, ScheduleWindow


class ScheduleProposalExecutor(BaseExecutor):
    route = "schedule-proposal"
    allowed_actions = frozenset({"create-schedule-proposal"})

    def __init__(
        self,
        job_store: JsonlJobStore,
        schedule_store: JsonlScheduleStore,
        receipt_store: JsonlReceiptStore,
    ) -> None:
        self.job_store = job_store
        self.schedule_store = schedule_store
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

        job = self.job_store.require(intent.subject_id)
        if job.status is not JobStatus.READY_TO_SCHEDULE:
            raise ValueError("job status changed before schedule proposal")

        proposal = ScheduleProposal(
            proposal_id=str(intent.parameters["proposal_id"]),
            job_id=job.job_id,
            timezone=str(intent.parameters["timezone"]),
            windows=tuple(
                ScheduleWindow(
                    start=datetime.fromisoformat(str(item[0])),
                    end=datetime.fromisoformat(str(item[1])),
                )
                for item in intent.parameters["windows"]
            ),
            notes=str(intent.parameters.get("notes", "")),
            metadata={
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )
        self.schedule_store.create(proposal)

        receipt = self.receipt_store.append(
            actor="Schedule Proposal Executor",
            decision="completed",
            executor="Schedule Proposal Executor",
            subject_id=job.job_id,
            details={
                "route": intent.route,
                "action": intent.action,
                "proposal_id": proposal.proposal_id,
                "job_id": job.job_id,
                "timezone": proposal.timezone,
                "window_count": len(proposal.windows),
                "proposal_only": True,
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "authorization_issued_at": authorization_issued_at,
                "authorization_expires_at": authorization_expires_at,
            },
        )
        return ExecutorResult(
            executor_name="Schedule Proposal Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={
                "proposal_id": proposal.proposal_id,
                "job_id": proposal.job_id,
                "window_count": len(proposal.windows),
                "proposal_only": True,
            },
        )
