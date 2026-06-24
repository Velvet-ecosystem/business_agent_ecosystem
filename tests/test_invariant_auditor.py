from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile
from business_agents.invariant_auditor import LifecycleInvariantAuditor


def write(path: Path, schema: str, payload: dict) -> None:
    CompatibleLockedJsonlFile(path, schema=schema).append(payload)


def test_empty_repository_is_clean(tmp_path: Path) -> None:
    report = LifecycleInvariantAuditor(tmp_path).audit()
    assert report.clean
    assert report.error_count == 0


def test_auditor_finds_cross_record_contradictions(tmp_path: Path) -> None:
    write(tmp_path / "jobs.jsonl", "job-event", {
        "job_id": "JOB-1", "customer_name": "Alex", "contact": "a@example.com",
        "request": "Install", "source": "manual", "status": "in-progress",
        "metadata": {}, "event_type": "transitioned",
    })
    write(tmp_path / "notification_drafts.jsonl", "notification-draft", {
        "draft_id": "DRAFT-1", "job_id": "JOB-404", "booking_id": "BOOK-404",
        "channel": "email", "recipient": "a@example.com", "subject": "Hi", "body": "Body",
    })
    write(tmp_path / "external_operations.jsonl", "external-operation-event", {
        "operation_id": "calendar:key-1", "provider": "calendar", "subject_id": "JOB-1",
        "idempotency_key": "key-1", "state": "provider-confirmed",
        "external_id": "evt-1", "local_record_id": None, "error": None, "metadata": {},
    })

    report = LifecycleInvariantAuditor(tmp_path).audit()
    codes = {finding.code for finding in report.findings}

    assert "advanced-job-without-booking" in codes
    assert "active-job-without-work-start" in codes
    assert "orphan-notification-draft" in codes
    assert "draft-missing-booking" in codes
    assert "external-operation-needs-reconciliation" in codes
    assert report.error_count == 4
    assert report.warning_count == 1
