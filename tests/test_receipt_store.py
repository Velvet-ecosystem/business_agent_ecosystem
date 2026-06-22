from dataclasses import replace
from pathlib import Path

import pytest

from business_agents.gateway.receipt_store import JsonlReceiptStore


def test_receipt_verification_detects_tampering(tmp_path: Path) -> None:
    store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    receipt = store.append(
        actor="Court",
        decision="denied",
        subject_id="small-workshop",
        details={"reason": "identity-not-verified"},
    )

    assert store.verify(receipt) is True

    tampered = replace(receipt, details={"reason": "approved"})
    assert store.verify(tampered) is False


def test_receipts_read_in_append_order(tmp_path: Path) -> None:
    store = JsonlReceiptStore(tmp_path / "receipts.jsonl")
    first = store.append(
        actor="Court",
        decision="denied",
        subject_id="one",
        details={"reason": "test"},
    )
    second = store.append(
        actor="Task Executor",
        decision="completed",
        executor="Task Executor",
        subject_id="two",
        details={"task_id": "task_0001"},
    )

    receipts = store.read_all()
    assert [receipt.receipt_id for receipt in receipts] == [
        first.receipt_id,
        second.receipt_id,
    ]
    assert all(store.verify(receipt) for receipt in receipts)


def test_invalid_jsonl_line_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    path.write_text('{"broken": true}\nnot-json\n', encoding="utf-8")
    store = JsonlReceiptStore(path)

    with pytest.raises(ValueError, match="invalid receipt at line 1"):
        store.read_all()
