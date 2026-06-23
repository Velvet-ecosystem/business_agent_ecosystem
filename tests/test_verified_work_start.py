from business_agents.agents.verified_work_start_agent import VerifiedWorkStartAgent


def test_verified_actor_is_used() -> None:
    proposal = VerifiedWorkStartAgent().propose({
        "start_id": "START-1",
        "job_id": "JOB-1",
        "booking_id": "BOOK-1",
        "started_by": "other",
        "reason": "Work bay ready",
        "job_status": "scheduled",
        "_principal_id": "owner-1",
        "_principal_display_name": "Mister",
    })
    assert proposal.intent.parameters["started_by"] == "owner-1"
