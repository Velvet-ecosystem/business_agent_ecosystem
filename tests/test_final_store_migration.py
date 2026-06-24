import json
from decimal import Decimal
from pathlib import Path

from business_agents.estimates import EstimateDraft, JsonlEstimateStore
from business_agents.gateway.receipt_store import JsonlReceiptStore
from business_agents.schedules import JsonlScheduleStore, ScheduleProposal, ScheduleWindow


def test_final_store_batch_writes_versioned_records(tmp_path: Path) -> None:
    from datetime import datetime

    schedules = JsonlScheduleStore(tmp_path / "schedules.jsonl")
    proposal = ScheduleProposal(
        proposal_id="PROP-1",
        job_id="JOB-1",
        timezone="America/Edmonton",
        windows=(ScheduleWindow(
            datetime.fromisoformat("2026-07-02T09:00:00-06:00"),
            datetime.fromisoformat("2026-07-02T10:00:00-06:00"),
        ),),
    )
    schedules.create(proposal)
    assert schedules.get("PROP-1") == proposal

    estimates = JsonlEstimateStore(tmp_path / "estimates.jsonl")
    estimate = EstimateDraft(
        "EST-1", "JOB-1", "CAD",
        Decimal("10.00"), Decimal("20.00"), Decimal("0.00"),
        Decimal("0.00"), Decimal("1.50"), Decimal("31.50"),
    )
    estimates.create(estimate)
    assert estimates.get("EST-1") == estimate

    receipts = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    receipt = receipts.append(
        actor="Court", decision="approved", subject_id="JOB-1", details={"ok": True}
    )
    assert receipts.verify(receipt)
    assert receipts.read_all() == [receipt]

    for name in ("schedules.jsonl", "estimates.jsonl", "receipts.jsonl"):
        first = json.loads((tmp_path / name).read_text(encoding="utf-8").splitlines()[0])
        assert "_schema" in first
        assert first["_version"] == 1
