from pathlib import Path

import pytest

from business_agents.communication_records import CommunicationRecord, CommunicationRecordStore
from business_agents.skills.customer_history_summary import CustomerHistorySummarySkill


def _record(
    record_id: str,
    customer_reference: str,
    job_id: str,
    channel: str,
    direction: str,
) -> CommunicationRecord:
    return CommunicationRecord(
        record_id=record_id,
        job_id=job_id,
        customer_reference=customer_reference,
        channel=channel,
        direction=direction,
        subject_reference=f"subject-{record_id}",
        content_reference=f"content-{record_id}",
        recorded_by="test",
    )


def test_customer_history_summary_is_read_only_and_minimized(tmp_path: Path) -> None:
    path = tmp_path / "communications.jsonl"
    store = CommunicationRecordStore(path)
    store.create(_record("rec-002", "cust-1", "job-2", "email", "outbound"))
    store.create(_record("rec-001", "cust-1", "job-1", "phone", "inbound"))
    store.create(_record("rec-003", "cust-2", "job-9", "email", "inbound"))

    before = path.read_text(encoding="utf-8")
    result = CustomerHistorySummarySkill(store).run({"customer_reference": "cust-1"})
    after = path.read_text(encoding="utf-8")

    assert result.status == "completed"
    assert result.output == {
        "customer_reference": "cust-1",
        "total_records": 2,
        "channel_counts": {"email": 1, "phone": 1},
        "direction_counts": {"inbound": 1, "outbound": 1},
        "job_ids": ("job-1", "job-2"),
        "records": (
            {"record_id": "rec-001", "job_id": "job-1", "channel": "phone", "direction": "inbound"},
            {"record_id": "rec-002", "job_id": "job-2", "channel": "email", "direction": "outbound"},
        ),
    }
    assert before == after
    rendered = repr(result.output)
    assert "subject-" not in rendered
    assert "content-" not in rendered
    assert "recorded_by" not in rendered


def test_customer_history_summary_requires_exact_input(tmp_path: Path) -> None:
    skill = CustomerHistorySummarySkill(CommunicationRecordStore(tmp_path / "communications.jsonl"))

    with pytest.raises(ValueError, match="requires only customer_reference"):
        skill.run({})
    with pytest.raises(ValueError, match="requires only customer_reference"):
        skill.run({"customer_reference": "cust-1", "extra": True})


def test_customer_lookup_validates_reference(tmp_path: Path) -> None:
    store = CommunicationRecordStore(tmp_path / "communications.jsonl")

    with pytest.raises(ValueError, match="customer_reference must be"):
        store.list_for_customer("")
