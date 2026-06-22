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
    integrity_method: str = "sha256"


class JsonlReceiptStore:
    """Writes receipts as one canonical JSON object per line."""

    def __init__(
        self,
        path: str | Path,
        *,
        signing_key: bytes | None = None,
        require_signing: bool = False,
    ) -> None:
        if require_signing and not signing_key:
            raise ValueError("signing_key is required when require_signing is enabled")
        self.path = Path(path)
        self.signing_key = signing_key
        self.require_signing = require_signing

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
        integrity_method = "hmac-sha256" if self.signing_key else "sha256"
        integrity_tag = self.calculate_integrity_tag(
            unsigned,
            method=integrity_method,
            signing_key=self.signing_key,
        )
        receipt = Receipt(
            **unsigned,
            integrity_tag=integrity_tag,
            integrity_method=integrity_method,
        )

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

    def verify(self, receipt: Receipt) -> bool:
        """Verify that a receipt is unchanged and, when signed, authentic."""
        unsigned = {
            "receipt_id": receipt.receipt_id,
            "created_at": receipt.created_at,
            "actor": receipt.actor,
            "decision": receipt.decision,
            "executor": receipt.executor,
            "subject_id": receipt.subject_id,
            "details": dict(receipt.details),
        }

        if receipt.integrity_method == "hmac-sha256" and not self.signing_key:
            return False
        if self.require_signing and receipt.integrity_method != "hmac-sha256":
            return False

        try:
            expected = self.calculate_integrity_tag(
                unsigned,
                method=receipt.integrity_method,
                signing_key=self.signing_key,
            )
        except ValueError:
            return False
        return hmac.compare_digest(expected, receipt.integrity_tag)

    @staticmethod
    def calculate_integrity_tag(
        unsigned: Mapping[str, Any],
        *,
        method: str,
        signing_key: bytes | None = None,
    ) -> str:
        canonical = json.dumps(
            dict(unsigned), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        if method == "sha256":
            return hashlib.sha256(canonical).hexdigest()
        if method == "hmac-sha256":
            if not signing_key:
                raise ValueError("signing_key is required for hmac-sha256")
            return hmac.new(signing_key, canonical, hashlib.sha256).hexdigest()
        raise ValueError("unsupported integrity method")
