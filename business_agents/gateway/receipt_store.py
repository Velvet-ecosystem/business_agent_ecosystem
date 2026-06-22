"""Append-only local receipt store for business-agent decisions and results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    created_at: str
    actor: str
    decision: str
    executor: str | None
    subject_id: str
    details: Mapping[str, Any]
    integrity_tag: str


class JsonlReceiptStore:
    """Writes receipts as one canonical JSON object per line."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        *,
        actor: str,
        decision: str,
        subject_id: str,
        details: Mapping[str, Any],
        executor: str | None = None,
    ) -> Receipt:
        created_at = datetime.now(timezone.utc).isoformat()
        receipt_id = f"rcpt_{uuid4().hex}"
        unsigned = {
            "receipt_id": receipt_id,
            "created_at": created_at,
            "actor": actor,
            "decision": decision,
            "executor": executor,
            "subject_id": subject_id,
            "details": dict(details),
        }
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
        integrity_tag = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        receipt = Receipt(**unsigned, integrity_tag=integrity_tag)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(receipt), sort_keys=True) + "\n")
        return receipt
