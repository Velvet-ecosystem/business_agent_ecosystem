"""Local receipt-signing key loading helpers."""

from __future__ import annotations

import os
from pathlib import Path

_MIN_KEY_BYTES = 32


def load_signing_key(
    *,
    env_name: str = "VELVET_RECEIPT_SIGNING_KEY",
    key_file: str | Path | None = None,
    required: bool = False,
) -> bytes | None:
    """Load a receipt-signing key from a file or environment variable.

    File input takes precedence over the environment variable. Whitespace around
    text keys is removed. Keys must be at least 32 bytes after UTF-8 encoding.
    """

    raw: str | None = None

    if key_file is not None:
        path = Path(key_file)
        if not path.is_file():
            raise FileNotFoundError(path)
        raw = path.read_text(encoding="utf-8").strip()
    else:
        value = os.environ.get(env_name)
        raw = value.strip() if value is not None else None

    if not raw:
        if required:
            raise ValueError("receipt signing key is required")
        return None

    key = raw.encode("utf-8")
    if len(key) < _MIN_KEY_BYTES:
        raise ValueError("receipt signing key must be at least 32 bytes")
    return key
