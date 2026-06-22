from pathlib import Path

import pytest

from business_agents.gateway.signing_key import load_signing_key


def test_loads_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VELVET_RECEIPT_SIGNING_KEY", "x" * 32)
    assert load_signing_key() == b"x" * 32


def test_file_key_takes_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VELVET_RECEIPT_SIGNING_KEY", "e" * 32)
    key_file = tmp_path / "receipt.key"
    key_file.write_text("f" * 32, encoding="utf-8")

    assert load_signing_key(key_file=key_file) == b"f" * 32


def test_required_key_fails_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VELVET_RECEIPT_SIGNING_KEY", raising=False)
    with pytest.raises(ValueError, match="receipt signing key is required"):
        load_signing_key(required=True)


def test_short_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VELVET_RECEIPT_SIGNING_KEY", "too-short")
    with pytest.raises(ValueError, match="at least 32 bytes"):
        load_signing_key()


def test_missing_key_file_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_signing_key(key_file=tmp_path / "missing.key")
