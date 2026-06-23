from pathlib import Path

from business_agents.compatible_storage import CompatibleLockedJsonlFile


def test_reads_legacy_and_versioned_lines(tmp_path: Path) -> None:
    path = tmp_path / "mixed.jsonl"
    path.write_text('{"record_id":"legacy"}\n', encoding="utf-8")
    store = CompatibleLockedJsonlFile(path, schema="mixed-record")
    store.append({"record_id": "versioned"})
    assert store.read_all() == [
        {"record_id": "legacy"},
        {"record_id": "versioned"},
    ]
