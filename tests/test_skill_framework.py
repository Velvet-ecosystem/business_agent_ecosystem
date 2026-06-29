from pathlib import Path

import pytest

from business_agents.contracts import ApprovalMode
from business_agents.jobs import JobRecord, JobStatus, JsonlJobStore
from business_agents.skills.contracts import SkillContract, SkillDomain, SkillEffect
from business_agents.skills.job_status_summary import JobStatusSummarySkill
from business_agents.skills.registry import SkillRegistry


def test_state_changing_skill_requires_capability_pair() -> None:
    with pytest.raises(ValueError, match="state-changing skills require"):
        SkillContract(
            skill_id="unsafe-skill",
            version="1.0.0",
            domain=SkillDomain.BUSINESS,
            effect=SkillEffect.STATE_CHANGING,
            approval_mode=ApprovalMode.HUMAN,
        )


def test_external_action_requires_receipt() -> None:
    with pytest.raises(ValueError, match="external actions require receipts"):
        SkillContract(
            skill_id="external-skill",
            version="1.0.0",
            domain=SkillDomain.COMMERCE,
            effect=SkillEffect.STATE_CHANGING,
            approval_mode=ApprovalMode.STRONG_HUMAN,
            capability_route="commerce.action",
            capability_action="publish",
            external_action=True,
            receipt_required=False,
        )


def test_registry_is_deterministic_and_rejects_duplicates(tmp_path: Path) -> None:
    skill = JobStatusSummarySkill(JsonlJobStore(tmp_path / "jobs.jsonl"))
    registry = SkillRegistry([skill])

    assert registry.get("job-status-summary") is skill
    assert tuple(contract.skill_id for contract in registry.list_contracts()) == (
        "job-status-summary",
    )
    with pytest.raises(ValueError, match="already registered"):
        registry.register(skill)


def test_job_status_summary_is_read_only_and_minimizes_output(tmp_path: Path) -> None:
    store = JsonlJobStore(tmp_path / "jobs.jsonl")
    store.create(
        JobRecord(
            job_id="job-002",
            customer_name="Customer Two",
            contact="private-two@example.test",
            request="Private request two",
            source="test",
        )
    )
    store.create(
        JobRecord(
            job_id="job-001",
            customer_name="Customer One",
            contact="private-one@example.test",
            request="Private request one",
            source="test",
        )
    )
    store.transition("job-001", JobStatus.APPROVED)

    before = (tmp_path / "jobs.jsonl").read_text(encoding="utf-8")
    result = JobStatusSummarySkill(store).run({})
    after = (tmp_path / "jobs.jsonl").read_text(encoding="utf-8")

    assert result.status == "completed"
    assert result.output == {
        "total_jobs": 2,
        "status_counts": {"approved": 1, "intake-review": 1},
        "jobs": (
            {"job_id": "job-001", "status": "approved"},
            {"job_id": "job-002", "status": "intake-review"},
        ),
    }
    assert before == after
    assert "contact" not in repr(result.output)
    assert "request" not in repr(result.output)


def test_job_status_summary_rejects_unexpected_inputs(tmp_path: Path) -> None:
    skill = JobStatusSummarySkill(JsonlJobStore(tmp_path / "jobs.jsonl"))

    with pytest.raises(ValueError, match="accepts no inputs"):
        skill.run({"status": "approved"})
