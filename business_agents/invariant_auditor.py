"""Read-only cross-record invariant auditor for the business lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.jobs import JobStatus


@dataclass(frozen=True)
class InvariantFinding:
    code: str
    severity: str
    subject_id: str
    message: str
    related_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuditReport:
    findings: tuple[InvariantFinding, ...]

    @property
    def clean(self) -> bool:
        return not self.findings

    @property
    def error_count(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(item.severity == "warning" for item in self.findings)


class LifecycleInvariantAuditor:
    """Audits stored records without changing them."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def audit(self) -> AuditReport:
        jobs = self._latest_by("jobs.jsonl", "job-event", "job_id")
        estimates = self._all("estimates.jsonl", "estimate-draft")
        schedules = self._all("schedules.jsonl", "schedule-proposal")
        preparations = self._all("booking_preparations.jsonl", "booking-preparation")
        bookings = self._all("bookings.jsonl", "booking-record")
        drafts = self._all("notification_drafts.jsonl", "notification-draft")
        deliveries = self._all("deliveries.jsonl", "delivery-record")
        starts = self._all("work_starts.jsonl", "work-start-record")
        operations = self._latest_by(
            "external_operations.jsonl",
            "external-operation-event",
            "operation_id",
        )

        findings: list[InvariantFinding] = []
        findings.extend(self._orphan_findings(jobs, estimates, schedules))
        findings.extend(self._booking_findings(jobs, schedules, preparations, bookings))
        findings.extend(self._notification_findings(jobs, bookings, drafts, deliveries))
        findings.extend(self._work_start_findings(jobs, bookings, starts))
        findings.extend(self._operation_findings(operations, bookings, deliveries))
        findings.sort(key=lambda item: (item.severity, item.code, item.subject_id))
        return AuditReport(tuple(findings))

    def _all(self, filename: str, schema: str) -> list[dict[str, Any]]:
        return CompatibleLockedJsonlFile(
            self.data_dir / filename,
            schema=schema,
        ).read_all()

    def _latest_by(self, filename: str, schema: str, field: str) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for item in self._all(filename, schema):
            value = str(item.get(field, ""))
            if value:
                latest[value] = item
        return latest

    @staticmethod
    def _orphan_findings(
        jobs: dict[str, dict[str, Any]],
        estimates: list[dict[str, Any]],
        schedules: list[dict[str, Any]],
    ) -> list[InvariantFinding]:
        findings: list[InvariantFinding] = []
        for record, kind, id_field in (
            (estimates, "estimate", "estimate_id"),
            (schedules, "schedule", "proposal_id"),
        ):
            for item in record:
                job_id = str(item.get("job_id", ""))
                if job_id not in jobs:
                    findings.append(InvariantFinding(
                        code=f"orphan-{kind}", severity="error",
                        subject_id=str(item.get(id_field, "unknown")),
                        message=f"{kind} references missing job {job_id}",
                        related_ids=(job_id,),
                    ))
        return findings

    @staticmethod
    def _booking_findings(jobs, schedules, preparations, bookings):
        findings: list[InvariantFinding] = []
        schedule_ids = {str(item.get("proposal_id")): item for item in schedules}
        preparation_ids = {str(item.get("preparation_id")): item for item in preparations}
        bookings_by_job: dict[str, list[dict[str, Any]]] = {}

        for prep in preparations:
            prep_id = str(prep.get("preparation_id", "unknown"))
            proposal = schedule_ids.get(str(prep.get("proposal_id")))
            if proposal is None:
                findings.append(InvariantFinding(
                    "orphan-booking-preparation", "error", prep_id,
                    "booking preparation references a missing schedule proposal",
                ))
            elif str(proposal.get("job_id")) != str(prep.get("job_id")):
                findings.append(InvariantFinding(
                    "preparation-job-mismatch", "error", prep_id,
                    "booking preparation and schedule proposal reference different jobs",
                ))

        for booking in bookings:
            booking_id = str(booking.get("booking_id", "unknown"))
            job_id = str(booking.get("job_id", ""))
            bookings_by_job.setdefault(job_id, []).append(booking)
            prep = preparation_ids.get(str(booking.get("preparation_id")))
            if job_id not in jobs:
                findings.append(InvariantFinding(
                    "orphan-booking", "error", booking_id,
                    f"booking references missing job {job_id}", (job_id,),
                ))
            if prep is None:
                findings.append(InvariantFinding(
                    "booking-missing-preparation", "error", booking_id,
                    "booking references a missing preparation",
                ))
            elif str(prep.get("job_id")) != job_id:
                findings.append(InvariantFinding(
                    "booking-job-mismatch", "error", booking_id,
                    "booking and preparation reference different jobs",
                ))

        for job_id, job in jobs.items():
            status = str(job.get("status", ""))
            count = len(bookings_by_job.get(job_id, []))
            if status in {JobStatus.SCHEDULED.value, JobStatus.IN_PROGRESS.value, JobStatus.COMPLETED.value} and count == 0:
                findings.append(InvariantFinding(
                    "advanced-job-without-booking", "error", job_id,
                    f"job is {status} but has no booking",
                ))
            if count > 1:
                findings.append(InvariantFinding(
                    "multiple-bookings-for-job", "error", job_id,
                    "job has more than one booking",
                    tuple(str(item.get("booking_id")) for item in bookings_by_job[job_id]),
                ))
        return findings

    @staticmethod
    def _notification_findings(jobs, bookings, drafts, deliveries):
        findings: list[InvariantFinding] = []
        booking_ids = {str(item.get("booking_id")): item for item in bookings}
        draft_ids = {str(item.get("draft_id")): item for item in drafts}
        delivery_by_draft: dict[str, list[dict[str, Any]]] = {}

        for draft in drafts:
            draft_id = str(draft.get("draft_id", "unknown"))
            job_id = str(draft.get("job_id", ""))
            booking = booking_ids.get(str(draft.get("booking_id")))
            if job_id not in jobs:
                findings.append(InvariantFinding(
                    "orphan-notification-draft", "error", draft_id,
                    f"notification draft references missing job {job_id}",
                ))
            if booking is None:
                findings.append(InvariantFinding(
                    "draft-missing-booking", "error", draft_id,
                    "notification draft references a missing booking",
                ))
            elif str(booking.get("job_id")) != job_id:
                findings.append(InvariantFinding(
                    "draft-job-mismatch", "error", draft_id,
                    "notification draft and booking reference different jobs",
                ))

        for delivery in deliveries:
            delivery_id = str(delivery.get("delivery_id", "unknown"))
            draft_id = str(delivery.get("draft_id", ""))
            delivery_by_draft.setdefault(draft_id, []).append(delivery)
            draft = draft_ids.get(draft_id)
            if draft is None:
                findings.append(InvariantFinding(
                    "orphan-delivery", "error", delivery_id,
                    "delivery references a missing notification draft",
                ))
            elif str(draft.get("job_id")) != str(delivery.get("job_id")):
                findings.append(InvariantFinding(
                    "delivery-job-mismatch", "error", delivery_id,
                    "delivery and notification draft reference different jobs",
                ))

        for draft_id, items in delivery_by_draft.items():
            if len(items) > 1:
                findings.append(InvariantFinding(
                    "multiple-deliveries-for-draft", "error", draft_id,
                    "notification draft has multiple delivery records",
                    tuple(str(item.get("delivery_id")) for item in items),
                ))
        return findings

    @staticmethod
    def _work_start_findings(jobs, bookings, starts):
        findings: list[InvariantFinding] = []
        booking_ids = {str(item.get("booking_id")): item for item in bookings}
        starts_by_job: dict[str, list[dict[str, Any]]] = {}
        for start in starts:
            start_id = str(start.get("start_id", "unknown"))
            job_id = str(start.get("job_id", ""))
            starts_by_job.setdefault(job_id, []).append(start)
            booking = booking_ids.get(str(start.get("booking_id")))
            if job_id not in jobs:
                findings.append(InvariantFinding(
                    "orphan-work-start", "error", start_id,
                    f"work start references missing job {job_id}",
                ))
            if booking is None:
                findings.append(InvariantFinding(
                    "work-start-missing-booking", "error", start_id,
                    "work start references a missing booking",
                ))
            elif str(booking.get("job_id")) != job_id:
                findings.append(InvariantFinding(
                    "work-start-job-mismatch", "error", start_id,
                    "work start and booking reference different jobs",
                ))

        for job_id, job in jobs.items():
            status = str(job.get("status", ""))
            count = len(starts_by_job.get(job_id, []))
            if status in {JobStatus.IN_PROGRESS.value, JobStatus.COMPLETED.value} and count == 0:
                findings.append(InvariantFinding(
                    "active-job-without-work-start", "error", job_id,
                    f"job is {status} but has no work-start record",
                ))
            if status not in {JobStatus.IN_PROGRESS.value, JobStatus.COMPLETED.value} and count > 0:
                findings.append(InvariantFinding(
                    "work-start-before-in-progress", "error", job_id,
                    f"job is {status} but already has a work-start record",
                ))
            if count > 1:
                findings.append(InvariantFinding(
                    "multiple-work-starts", "error", job_id,
                    "job has multiple work-start records",
                ))
        return findings

    @staticmethod
    def _operation_findings(operations, bookings, deliveries):
        findings: list[InvariantFinding] = []
        booking_ids = {str(item.get("booking_id")) for item in bookings}
        delivery_ids = {str(item.get("delivery_id")) for item in deliveries}
        for operation_id, operation in operations.items():
            state = str(operation.get("state", ""))
            local_id = str(operation.get("local_record_id") or "")
            if state == "provider-confirmed":
                findings.append(InvariantFinding(
                    "external-operation-needs-reconciliation", "warning", operation_id,
                    "provider confirmed the operation but no local record was completed",
                ))
            if state == "locally-recorded":
                provider = str(operation.get("provider", ""))
                expected = booking_ids if provider == "calendar" else delivery_ids
                if local_id not in expected:
                    findings.append(InvariantFinding(
                        "operation-local-record-missing", "error", operation_id,
                        f"operation claims local record {local_id}, but it does not exist",
                        (local_id,),
                    ))
        return findings
