from pathlib import Path

from business_agents.external_operations import ExternalOperationJournal, ExternalOperationState


def test_operation_milestones(tmp_path: Path) -> None:
    journal = ExternalOperationJournal(tmp_path / "operations.jsonl")
    operation = journal.prepare(
        operation_id="calendar-key-1",
        provider="calendar",
        subject_id="JOB-1",
        idempotency_key="key-1",
    )
    assert operation.state is ExternalOperationState.PREPARED
    operation = journal.provider_confirmed("calendar-key-1", external_id="evt-1")
    assert journal.pending_reconciliation() == (operation,)
    operation = journal.locally_recorded("calendar-key-1", local_record_id="BOOK-1")
    assert operation.state is ExternalOperationState.LOCALLY_RECORDED
    assert journal.pending_reconciliation() == ()
