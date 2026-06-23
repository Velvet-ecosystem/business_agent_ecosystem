from pathlib import Path

from business_agents.locked_artifact_stores import (
    LockedBookingPreparationStore,
    LockedDeliveryStore,
    LockedNotificationDraftStore,
    LockedWorkStartStore,
)


def build_store_bundle(data_dir: Path) -> dict[str, object]:
    data_dir.mkdir(parents=True, exist_ok=True)
    return {
        "preparations": LockedBookingPreparationStore(data_dir / "booking_preparations.jsonl"),
        "drafts": LockedNotificationDraftStore(data_dir / "notification_drafts.jsonl"),
        "deliveries": LockedDeliveryStore(data_dir / "deliveries.jsonl"),
        "starts": LockedWorkStartStore(data_dir / "work_starts.jsonl"),
    }
