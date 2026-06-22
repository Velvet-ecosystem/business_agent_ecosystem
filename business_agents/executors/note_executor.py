"""Executor for approved local internal operations notes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from business_agents.contracts import BusinessIntent, ExecutorResult
from business_agents.executors.base_executor import BaseExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore


@dataclass(frozen=True)
class InternalNote:
    note_id: str
    title: str
    body: str
    subject_id: str
    metadata: Mapping[str, Any]


class NoteExecutor(BaseExecutor):
    route = "internal-note"
    allowed_actions = frozenset({"record-operations-note"})

    def __init__(self, receipt_store: JsonlReceiptStore) -> None:
        self.receipt_store = receipt_store
        self.notes: list[InternalNote] = []

    def execute(
        self,
        intent: BusinessIntent,
        *,
        authorization_id: str,
        authorization_fingerprint: str,
    ) -> ExecutorResult:
        if not authorization_id.strip():
            raise ValueError("authorization_id is required")
        if not authorization_fingerprint.strip():
            raise ValueError("authorization_fingerprint is required")
        if not self.supports(intent):
            raise ValueError("unsupported intent")

        title = str(intent.parameters["title"]).strip()
        body = str(intent.parameters["body"]).strip()
        note = InternalNote(
            note_id=f"note_{len(self.notes) + 1:04d}",
            title=title,
            body=body,
            subject_id=intent.subject_id,
            metadata={
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
            },
        )

        receipt = self.receipt_store.append(
            actor="Note Executor",
            decision="completed",
            executor="Note Executor",
            subject_id=intent.subject_id,
            details={
                "authorization_id": authorization_id,
                "authorization_fingerprint": authorization_fingerprint,
                "route": intent.route,
                "action": intent.action,
                "note_id": note.note_id,
                "title": note.title,
            },
        )
        self.notes.append(note)

        return ExecutorResult(
            executor_name="Note Executor",
            status="completed",
            receipt_id=receipt.receipt_id,
            output={"note_id": note.note_id, "title": note.title},
        )
