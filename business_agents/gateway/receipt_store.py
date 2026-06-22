"""Append-only local receipt store for business-agent decisions and results."""

from __future__ import annotations

import hashlib
import hmac
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
        integrity_tag = self.calculate_integrity_tag(unsigned)
        receipt = Receipt(**unsigned, integrity_tag=integrity_tag)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(receipt), sort_keys=True) + "\n")
        return receipt

    def read_all(self) -> list[Receipt]:
        """Read all stored receipts in append order."""
        if not self.path.exists():
            return []

        receipts: list[Receipt] = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                receipts.append(Receipt(**data))
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValueError(f"invalid receipt at line {line_number}") from exc
        return receipts

    @classmethod
    def verify(cls, receipt: Receipt) -> bool:
        """Independently verify that a receipt's canonical content is unchanged."""
        unsigned = {
            "receipt_id": receipt.receipt_id,
            "created_at": receipt.created_at,
            "actor": receipt.actor,
            "decision": receipt.decision,
            "executor": receipt.executor,
            "subject_id": receipt.subject_id,
            "details": dict(receipt.details),
        }
        expected = cls.calculate_integrity_tag(unsigned)
        return hmac.compare_digest(expected, receipt.integrity_tag)

    @staticmethod
    def calculate_integrity_tag(unsigned: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            dict(unsigned), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
