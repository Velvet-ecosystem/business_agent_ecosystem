from pathlib import Path

import pytest

from business_agents.notifications import JsonlNotificationDraftStore
from business_agents.skills.prepare_booking_confirmation import PrepareBookingConfirmationSkill


def test_prepare_booking_confirmation_returns_proposal_only(tmp_path: Path) -> None:
    draft_path = tmp_path / "notification_drafts.jsonl"
    store = JsonlNotificationDraftStore(draft_path)
    skill = PrepareBookingConfirmationSkill()

    result = skill.run(
        {
            "draft_id": "draft-001",
            "booking_id": "booking-001",
            "job_id": "job-001",
            "job_status": "scheduled",
        }
    )

    proposal = result.output["proposal"]
    assert result.status == "completed"
    assert proposal["route"] == "notification-draft"
    assert proposal["action"] == "create-booking-confirmation-draft"
    assert proposal["subject_id"] == "job-001"
    assert proposal["approval_mode"] == "human"
    assert proposal["authority_granted"] is False
    assert result.output["send_authority"] is False
    assert result.artifacts == ("agent-proposal",)
    assert store.get("draft-001") is None
    assert not draft_path.exists()


def test_prepare_booking_confirmation_requires_exact_inputs() -> None:
    skill = PrepareBookingConfirmationSkill()

    with pytest.raises(ValueError, match="exact declared inputs"):
        skill.run(
            {
                "draft_id": "draft-001",
                "booking_id": "booking-001",
                "job_id": "job-001",
                "job_status": "scheduled",
                "send": True,
            }
        )


def test_prepare_booking_confirmation_requires_scheduled_job() -> None:
    skill = PrepareBookingConfirmationSkill()

    with pytest.raises(ValueError, match="job must be scheduled"):
        skill.run(
            {
                "draft_id": "draft-001",
                "booking_id": "booking-001",
                "job_id": "job-001",
                "job_status": "approved",
            }
        )
