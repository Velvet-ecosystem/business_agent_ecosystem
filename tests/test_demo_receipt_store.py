from pathlib import Path

from business_agents.gateway.chained_receipt_store import ChainedReceiptStore


def test_recommended_store_writes_a_valid_chain(tmp_path: Path) -> None:
    store = ChainedReceiptStore(tmp_path / "receipts.jsonl")
    first = store.append(
        actor="Court",
        decision="approved",
        subject_id="small-workshop",
        details={"authorization_id": "auth:test"},
    )
    second = store.append(
        actor="Task Executor",
        decision="completed",
        executor="Task Executor",
        subject_id="small-workshop",
        details={"task_id": "task_0001"},
    )

    assert first.receipt_id != second.receipt_id
    assert store.verify_chain() is True
