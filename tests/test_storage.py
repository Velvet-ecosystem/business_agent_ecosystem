"""Tests for the shared locked JSONL persistence primitive."""

from pathlib import Path

import pytest

from business_agents.storage import JsonlCorruptionError, LockedJsonlFile


def test_append_and_read_versioned_records(tmp_path: Path) -> None:
    store = LockedJsonlFile(tmp_path / "records.jsonl", schema="test-record")

    store.append({"record_id": "A", "value": 1})
    store.append({"record_id": "B", "value": 2})

    assert store.read_all() == [
        {"record_id": "A", "value": 1},
        {"record_id": "B", "value": 2},
    ]


def test_append_unique_rejects_duplicate_field(tmp_path: Path) -> None:
    store = LockedJsonlFile(tmp_path / "records.jsonl", schema="test-record")

    store.append_unique({"record_id": "A"}, field="record_id")

    with pytest.raises(ValueError, match="already exists"):
        store.append_unique({"record_id": "A"}, field="record_id")


def test_corrupt_json_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text("not-json\n", encoding="utf-8")
    store = LockedJsonlFile(path, schema="test-record")

    with pytest.raises(JsonlCorruptionError, match="invalid JSONL"):
        store.read_all()


def test_wrong_schema_is_detected(tmp_path: Path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text(
        '{"_schema":"other","_version":1,"data":{"record_id":"A"}}\n',
        encoding="utf-8",
    )
    store = LockedJsonlFile(path, schema="test-record")

    with pytest.raises(JsonlCorruptionError, match="unexpected schema"):
        store.read_all()


def test_lock_file_is_separate_from_data_file(tmp_path: Path) -> None:
    store = LockedJsonlFile(tmp_path / "records.jsonl", schema="test-record")
    store.append({"record_id": "A"})

    assert store.path.exists()
    assert store.lock_path.exists()
    assert store.lock_path != store.path
