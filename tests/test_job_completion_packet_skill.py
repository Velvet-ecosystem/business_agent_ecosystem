from pathlib import Path

import pytest

from business_agents.completion_evidence import CompletionEvidence, CompletionEvidenceStore
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.skills.job_completion_packet import JobCompletionPacketSkill


def _completed_job(store: JsonlJobStore, job_id: str) -> None:
    store.create(
        JobRecord(
            job_id=job_id,
            customer_name="Private Customer",
            contact="private@example.test",
            request="Private request details",
            source="test",
        )
    )
    for status in (
        JobStatus.APPROVED,
        JobStatus.ESTIMATING,
        JobStatus.READY_TO_SCHEDULE,
        JobStatus.SCHEDULED,
        JobStatus.IN_PROGRESS,
        JobStatus.COMPLETED,
    ):
        store.transition(job_id, status)


def test_job_completion_packet_is_internal_read_only_and_minimized(tmp_path: Path) -> None:
    job_path = tmp_path / "jobs.jsonl"
    evidence_path = tmp_path / "completion.jsonl"
    jobs = JsonlJobStore(job_path)
    evidence = CompletionEvidenceStore(evidence_path)
    _completed_job(jobs, "job-001")
    evidence.create(
        CompletionEvidence(
            evidence_id="evidence-001",
            job_id="job-001",
            completed_by="tech-1",
            summary="Work completed and verified.",
            checklist=("inspection passed", "workspace cleared"),
            artifact_refs=("artifact://photo-1", "artifact://test-report-1"),
            customer_acknowledged=True,
            metadata={"private_note": "must not appear"},
        )
    )

    before_jobs = job_path.read_text(encoding="utf-8")
    before_evidence = evidence_path.read_text(encoding="utf-8")
    result = JobCompletionPacketSkill(jobs, evidence).run({"job_id": "job-001"})

    assert result.output == {
        "packet": {
            "job_id": "job-001",
            "status": "completed",
            "evidence_id": "evidence-001",
            "completed_by": "tech-1",
            "summary": "Work completed and verified.",
            "checklist": ("inspection passed", "workspace cleared"),
            "artifact_refs": ("artifact://photo-1", "artifact://test-report-1"),
            "customer_acknowledged": True,
        },
        "delivery_authority": False,
    }
    assert result.artifacts == ("internal-completion-packet",)
    assert job_path.read_text(encoding="utf-8") == before_jobs
    assert evidence_path.read_text(encoding="utf-8") == before_evidence
    rendered = repr(result.output)
    assert "private@example.test" not in rendered
    assert "Private request details" not in rendered
    assert "private_note" not in rendered


def test_job_completion_packet_requires_completed_job(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    evidence = CompletionEvidenceStore(tmp_path / "completion.jsonl")
    jobs.create(
        JobRecord(
            job_id="job-001",
            customer_name="Customer",
            contact="contact@example.test",
            request="Request",
            source="test",
        )
    )

    with pytest.raises(ValueError, match="job must be completed"):
        JobCompletionPacketSkill(jobs, evidence).run({"job_id": "job-001"})


def test_job_completion_packet_requires_evidence(tmp_path: Path) -> None:
    jobs = JsonlJobStore(tmp_path / "jobs.jsonl")
    evidence = CompletionEvidenceStore(tmp_path / "completion.jsonl")
    _completed_job(jobs, "job-001")

    with pytest.raises(ValueError, match="completion evidence not found"):
        JobCompletionPacketSkill(jobs, evidence).run({"job_id": "job-001"})


def test_job_completion_packet_rejects_extra_inputs(tmp_path: Path) -> None:
    skill = JobCompletionPacketSkill(
        JsonlJobStore(tmp_path / "jobs.jsonl"),
        CompletionEvidenceStore(tmp_path / "completion.jsonl"),
    )

    with pytest.raises(ValueError, match="requires only job_id"):
        skill.run({"job_id": "job-001", "send": True})
