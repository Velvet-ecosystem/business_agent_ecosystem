"""Append-only stock reservation records for jobs."""

from dataclasses import asdict, dataclass
from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


@dataclass(frozen=True)
class StockReservation:
    reservation_id: str
    job_id: str
    item_reference: str
    quantity_reference: str
    location_reference: str
    reserved_by: str

    def __post_init__(self) -> None:
        for name in ("reservation_id", "job_id", "item_reference", "quantity_reference", "location_reference", "reserved_by"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


class StockReservationStore:
    def __init__(self, path: Path) -> None:
        self._storage = CompatibleLockedJsonlFile(path, schema="stock-reservation")

    def create(self, record: StockReservation) -> StockReservation:
        self._storage.append_unique(asdict(record), field="reservation_id")
        return record

    def get(self, reservation_id: str) -> StockReservation | None:
        for payload in reversed(self._storage.read_all()):
            if payload.get("reservation_id") == reservation_id:
                return StockReservation(**payload)
        return None
