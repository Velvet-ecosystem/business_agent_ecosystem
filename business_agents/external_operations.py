"""Durable reconciliation journal for external provider writes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from business_agents.compatible_storage import CompatibleLockedJsonlFile


class ExternalOperationState(str, Enum):
    PREPARED = "prepared"
    PROVIDER_CONFIRMED = "provider-confirmed"
    LOCALLY_RECORDED = "locally-recorded"
    FAILED = "failed"


@dataclass(frozen=True)
class ExternalOperation:
    operation_id: str
    provider: str
    subject_id: str
    idempotency_key: str
    state: ExternalOperationState
    external_id: str | None = None
    local_record_id: str | None = None
    error: str | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("operation_id", self.operation_id),
            ("provider", self.provider),
            ("subject_id", self.subject_id),
            ("idempotency_key", self.idempotency_key),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.state, ExternalOperationState):
            raise ValueError("state must be an ExternalOperationState")
        if self.metadata is not None and not isinstance(self.metadata, Mapping):
            raise ValueError("metadata must be a mapping")


class ExternalOperationJournal:
    """Append-only state journal reconstructed by operation ID."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._storage = CompatibleLockedJsonlFile(
            path,
            schema="external-operation-event",
            version=1,
        )

    def prepare(
        self,
        *,
        operation_id: str,
        provider: str,
        subject_id: str,
        idempotency_key: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> ExternalOperation:
        with self._storage.locked_file.locked():
            existing = self._get_unlocked(operation_id)
            if existing is not None:
                if (
                    existing.provider != provider
                    or existing.subject_id != subject_id
                    or existing.idempotency_key != idempotency_key
                ):
                    raise ValueError("operation ID is bound to different parameters")
                return existing
            operation = ExternalOperation(
                operation_id=operation_id,
                provider=provider,
                subject_id=subject_id,
                idempotency_key=idempotency_key,
                state=ExternalOperationState.PREPARED,
                metadata=dict(metadata or {}),
            )
            self._append_unlocked(operation)
            return operation

    def provider_confirmed(self, operation_id: str, *, external_id: str) -> ExternalOperation:
        if not external_id.strip():
            raise ValueError("external_id is required")
        with self._storage.locked_file.locked():
            current = self._require_unlocked(operation_id)
            if current.state is ExternalOperationState.LOCALLY_RECORDED:
                return current
            if current.state not in {
                ExternalOperationState.PREPARED,
                ExternalOperationState.PROVIDER_CONFIRMED,
            }:
                raise ValueError("operation cannot be provider-confirmed")
            updated = replace(
                current,
                state=ExternalOperationState.PROVIDER_CONFIRMED,
                external_id=external_id,
                error=None,
            )
            self._append_unlocked(updated)
            return updated

    def locally_recorded(self, operation_id: str, *, local_record_id: str) -> ExternalOperation:
        if not local_record_id.strip():
            raise ValueError("local_record_id is required")
        with self._storage.locked_file.locked():
            current = self._require_unlocked(operation_id)
            if current.state is ExternalOperationState.LOCALLY_RECORDED:
                if current.local_record_id != local_record_id:
                    raise ValueError("operation already bound to another local record")
                return current
            if current.state is not ExternalOperationState.PROVIDER_CONFIRMED:
                raise ValueError("provider confirmation is required first")
            updated = replace(
                current,
                state=ExternalOperationState.LOCALLY_RECORDED,
                local_record_id=local_record_id,
                error=None,
            )
            self._append_unlocked(updated)
            return updated

    def failed(self, operation_id: str, *, error: str) -> ExternalOperation:
        if not error.strip():
            raise ValueError("error is required")
        with self._storage.locked_file.locked():
            current = self._require_unlocked(operation_id)
            updated = replace(
                current,
                state=ExternalOperationState.FAILED,
                error=error,
            )
            self._append_unlocked(updated)
            return updated

    def get(self, operation_id: str) -> ExternalOperation | None:
        with self._storage.locked_file.locked():
            return self._get_unlocked(operation_id)

    def pending_reconciliation(self) -> tuple[ExternalOperation, ...]:
        latest: dict[str, ExternalOperation] = {}
        for payload in self._storage.read_all():
            operation = self._from_payload(payload)
            latest[operation.operation_id] = operation
        return tuple(
            latest[key]
            for key in sorted(latest)
            if latest[key].state is ExternalOperationState.PROVIDER_CONFIRMED
        )

    def _get_unlocked(self, operation_id: str) -> ExternalOperation | None:
        current = None
        for payload in self._storage._read_all_unlocked():
            if payload.get("operation_id") == operation_id:
                current = self._from_payload(payload)
        return current

    def _require_unlocked(self, operation_id: str) -> ExternalOperation:
        operation = self._get_unlocked(operation_id)
        if operation is None:
            raise KeyError(f"external operation not found: {operation_id}")
        return operation

    def _append_unlocked(self, operation: ExternalOperation) -> None:
        import json
        import os

        payload = asdict(operation)
        payload["state"] = operation.state.value
        payload["metadata"] = dict(operation.metadata or {})
        envelope = {
            "_schema": "external-operation-event",
            "_version": 1,
            "data": payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _from_payload(payload: Mapping[str, Any]) -> ExternalOperation:
        return ExternalOperation(
            operation_id=str(payload["operation_id"]),
            provider=str(payload["provider"]),
            subject_id=str(payload["subject_id"]),
            idempotency_key=str(payload["idempotency_key"]),
            state=ExternalOperationState(str(payload["state"])),
            external_id=(str(payload["external_id"]) if payload.get("external_id") else None),
            local_record_id=(
                str(payload["local_record_id"])
                if payload.get("local_record_id")
                else None
            ),
            error=(str(payload["error"]) if payload.get("error") else None),
            metadata=dict(payload.get("metadata", {})),
        )
