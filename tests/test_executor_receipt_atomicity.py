from typing import Any

import pytest

from business_agents.contracts import BusinessIntent
from business_agents.executors.note_executor import NoteExecutor
from business_agents.executors.task_executor import TaskExecutor
from business_agents.gateway.receipt_store import JsonlReceiptStore


class FailingReceiptStore:
    def append(self, **_: Any):
        raise OSError("simulated receipt write failure")


def authorization_kwargs() -> dict[str, object]:
    return {
        "authorization_id": "auth_test",
        "authorization_fingerprint": "a" * 64,
        "authorization_issued_at": 1000.0,
        "authorization_expires_at": 1030.0,
    }


def task_intent() -> BusinessIntent:
    return BusinessIntent(
        route="internal-task",
        action="create-restock-review",
        subject_id="small-workshop",
        parameters={"sku": "FILTER-001", "suggested_quantity": 12},
    )


def note_intent() -> BusinessIntent:
    return BusinessIntent(
        route="internal-note",
        action="record-operations-note",
        subject_id="small-workshop",
        parameters={
            "title": "Printer maintenance",
            "body": "Cleaned the rails and checked belt tension.",
        },
    )


def test_task_does_not_survive_failed_receipt_append() -> None:
    executor = TaskExecutor(FailingReceiptStore())  # type: ignore[arg-type]

    with pytest.raises(OSError, match="receipt write failure"):
        executor.execute(task_intent(), **authorization_kwargs())

    assert executor.tasks == []


def test_note_does_not_survive_failed_receipt_append() -> None:
    executor = NoteExecutor(FailingReceiptStore())  # type: ignore[arg-type]

    with pytest.raises(OSError, match="receipt write failure"):
        executor.execute(note_intent(), **authorization_kwargs())

    assert executor.notes == []


def test_failed_task_write_does_not_consume_task_sequence(tmp_path) -> None:
    failing = TaskExecutor(FailingReceiptStore())  # type: ignore[arg-type]
    with pytest.raises(OSError):
        failing.execute(task_intent(), **authorization_kwargs())

    healthy = TaskExecutor(JsonlReceiptStore(tmp_path / "receipts.jsonl"))
    result = healthy.execute(task_intent(), **authorization_kwargs())

    assert result.output["task_id"] == "task_0001"
    assert healthy.tasks[0].task_id == "task_0001"


def test_failed_note_write_does_not_consume_note_sequence(tmp_path) -> None:
    failing = NoteExecutor(FailingReceiptStore())  # type: ignore[arg-type]
    with pytest.raises(OSError):
        failing.execute(note_intent(), **authorization_kwargs())

    healthy = NoteExecutor(JsonlReceiptStore(tmp_path / "receipts.jsonl"))
    result = healthy.execute(note_intent(), **authorization_kwargs())

    assert result.output["note_id"] == "note_0001"
    assert healthy.notes[0].note_id == "note_0001"
