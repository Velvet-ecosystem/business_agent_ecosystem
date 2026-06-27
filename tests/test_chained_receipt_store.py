import json
from pathlib import Path

from business_agents.gateway.chained_receipt_store import ChainedReceiptStore


def test_chain_verifies_in_append_order(tmp_path: Path) -> None:
    store = ChainedReceiptStore(tmp_path / "receipts.jsonl")
    store.append(actor="Court", decision="approved", subject_id="one", details={"authorization_id": "auth:one"})
    store.append(actor="Task Executor", decision="completed", executor="Task Executor", subject_id="two", details={"task_id": "task_0001"})
    assert store.verify_chain() is True


def test_chain_detects_missing_middle_record(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    store = ChainedReceiptStore(path)
    for index in range(3):
        store.append(actor="Court", decision="approved", subject_id=str(index), details={"index": index})
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")
    assert store.verify_chain() is False


def test_chain_detects_reordered_records(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    store = ChainedReceiptStore(path)
    store.append(actor="Court", decision="approved", subject_id="one", details={"index": 1})
    store.append(actor="Court", decision="approved", subject_id="two", details={"index": 2})
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(reversed(lines)) + "\n", encoding="utf-8")
    assert store.verify_chain() is False


def test_chain_detects_link_tampering(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    store = ChainedReceiptStore(path)
    store.append(actor="Court", decision="approved", subject_id="one", details={"index": 1})
    store.append(actor="Court", decision="approved", subject_id="two", details={"index": 2})
    lines = path.read_text(encoding="utf-8").splitlines()
    second = json.loads(lines[1])
    second["data"]["details"]["_previous_integrity_tag"] = "wrong"
    lines[1] = json.dumps(second, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert store.verify_chain() is False
