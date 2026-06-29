from pathlib import Path

import pytest

from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.skills.business_daily_brief import BusinessDailyBriefSkill


def _job(job_id: str) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        customer_name=f"Customer {job_id}",
        contact=f"{job_id}@example.test",
        request=f"Private request {job_id}",
        source="test",
    )


def test_business_daily_brief_is_current_read_only_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "jobs.jsonl"
    store = JsonlJobStore(path)
    store.create(_job("job-001"))
    store.create(_job("job-002"))
    store.create(_job("job-003"))
    store.transition("job-002", JobStatus.APPROVED)
    store.transition("job-003", JobStatus.APPROVED)
    store.transition("job-003", JobStatus.ESTIMATING)
    store.transition("job-003", JobStatus.READY_TO_SCHEDULE)
    store.transition("job-003", JobStatus.SCHEDULED)
    store.transition("job-003", JobStatus.IN_PROGRESS)
    store.transition("job-003", JobStatus.COMPLETED)

    before = path.read_text(encoding="utf-8")
    result = BusinessDailyBriefSkill(store).run({})
    after = path.read_text(encoding="utf-8")

    assert result.status == "completed"
    assert result.output == {
        "scope": "current-snapshot",
        "total_jobs": 3,
        "active_jobs": 2,
        "terminal_jobs": 1,
        "status_counts": {"approved": 1, "completed": 1, "intake-review": 1},
        "attention_jobs": (
            {"job_id": "job-001", "status": "intake-review"},
            {"job_id": "job-002", "status": "approved"},
        ),
    }
    assert before == after
    rendered = repr(result.output)
    assert "contact" not in rendered
    assert "Private request" not in rendered
    assert "changed_today" not in rendered


def test_business_daily_brief_rejects_inputs(tmp_path: Path) -> None:
    skill = BusinessDailyBriefSkill(JsonlJobStore(tmp_path / "jobs.jsonl"))

    with pytest.raises(ValueError, match="accepts no inputs"):
        skill.run({"date": "2026-06-29"})
