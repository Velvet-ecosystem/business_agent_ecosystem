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


def test_hmac_receipt_requires_matching_key(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    signing_store = JsonlReceiptStore(path, signing_key=b"local-test-key")
    receipt = signing_store.append(
        actor="Court",
        decision="approved",
        subject_id="small-workshop",
        details={"authorization_id": "auth:test"},
    )

    assert receipt.integrity_method == "hmac-sha256"
    assert signing_store.verify(receipt) is True
    assert JsonlReceiptStore(path).verify(receipt) is False
    assert JsonlReceiptStore(path, signing_key=b"wrong-key").verify(receipt) is False


def test_required_signing_rejects_missing_key(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="signing_key is required"):
        JsonlReceiptStore(tmp_path / "receipts.jsonl", require_signing=True)


def test_required_signing_rejects_unsigned_receipt(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    unsigned_store = JsonlReceiptStore(path)
    unsigned = unsigned_store.append(
        actor="Court",
        decision="denied",
        subject_id="small-workshop",
        details={"reason": "test"},
    )

    strict_store = JsonlReceiptStore(
        path,
        signing_key=b"local-test-key",
        require_signing=True,
    )
    assert strict_store.verify(unsigned) is False
