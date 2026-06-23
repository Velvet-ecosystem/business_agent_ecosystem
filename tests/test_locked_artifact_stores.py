from datetime import datetime
from pathlib import Path

from business_agents.bookings import BookingPreparation
from business_agents.delivery_records import DeliveryRecord
from business_agents.locked_artifact_stores import LockedBookingPreparationStore, LockedDeliveryStore, LockedNotificationDraftStore, LockedWorkStartStore
from business_agents.notifications import NotificationDraft
from business_agents.work_start import WorkStartRecord


def test_locked_artifact_stores_round_trip(tmp_path: Path) -> None:
    prep_store = LockedBookingPreparationStore(tmp_path / "prep.jsonl")
    prep = BookingPreparation(
        "PREP-1", "PROP-1", "JOB-1", 0,
        datetime.fromisoformat("2026-07-02T09:00:00-06:00"),
        datetime.fromisoformat("2026-07-02T10:00:00-06:00"),
        "America/Edmonton",
    )
    assert prep_store.create(prep) == prep
    assert prep_store.get("PREP-1") == prep

    draft_store = LockedNotificationDraftStore(tmp_path / "draft.jsonl")
    draft = NotificationDraft("NOTE-1", "JOB-1", "BOOK-1", "email", "a@example.com", "Subject", "Body")
    assert draft_store.create(draft) == draft
    assert draft_store.get("NOTE-1") == draft

    delivery_store = LockedDeliveryStore(tmp_path / "delivery.jsonl")
    delivery = DeliveryRecord("DEL-1", "NOTE-1", "JOB-1", "key-1", "msg-1")
    assert delivery_store.create(delivery) == delivery
    assert delivery_store.get_by_idempotency_key("key-1") == delivery

    start_store = LockedWorkStartStore(tmp_path / "start.jsonl")
    start = WorkStartRecord("START-1", "JOB-1", "BOOK-1", "owner-1", "Ready")
    assert start_store.create(start) == start
    assert start_store.get_by_job("JOB-1") == start
