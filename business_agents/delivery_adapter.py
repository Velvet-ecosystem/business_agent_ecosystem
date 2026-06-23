"""Provider boundary for idempotent notification delivery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DeliveryRequest:
    idempotency_key: str
    recipient: str
    subject: str
    body: str


@dataclass(frozen=True)
class DeliveryResult:
    provider_message_id: str
    idempotency_key: str
    created_now: bool


class DeliveryAdapter(Protocol):
    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        """Deliver or return the message bound to one idempotency key."""


class InMemoryDeliveryAdapter:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.results: dict[str, DeliveryResult] = {}
        self.requests: dict[str, DeliveryRequest] = {}

    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        if self.fail:
            raise RuntimeError("delivery adapter failure")
        existing = self.results.get(request.idempotency_key)
        if existing is not None:
            return DeliveryResult(existing.provider_message_id, existing.idempotency_key, False)
        result = DeliveryResult(
            provider_message_id=f"msg_{len(self.results) + 1:04d}",
            idempotency_key=request.idempotency_key,
            created_now=True,
        )
        self.results[request.idempotency_key] = result
        self.requests[request.idempotency_key] = request
        return result
