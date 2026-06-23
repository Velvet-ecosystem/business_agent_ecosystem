"""Durable bindings between notification drafts and provider messages."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DeliveryRecord:
    delivery_id: str
    draft_id: str
    job_id: str
    idempotency_key: str
    provider_message_id: str


class JsonlDeliveryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, record: DeliveryRecord) -> DeliveryRecord:
        existing = self.get_by_idempotency_key(record.idempotency_key)
        if existing is not None:
            if existing != record:
                raise ValueError("idempotency key already bound to another delivery")
            return existing
        if self.get(record.delivery_id) is not None:
            raise ValueError(f"delivery already exists: {record.delivery_id}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")
        return record

    def get(self, delivery_id: str) -> DeliveryRecord | None:
        return self._find("delivery_id", delivery_id)

    def get_by_idempotency_key(self, key: str) -> DeliveryRecord | None:
        return self._find("idempotency_key", key)

    def _find(self, field: str, value: str) -> DeliveryRecord | None:
        if not self.path.exists():
            return None
        found = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                if payload.get(field) == value:
                    found = DeliveryRecord(**payload)
        return found
