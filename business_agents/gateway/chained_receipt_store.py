"""Receipt-store wrapper that links each record to the previous one."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from business_agents.gateway.receipt_store import JsonlReceiptStore, Receipt


class ChainedReceiptStore(JsonlReceiptStore):
    """Adds sequence and previous-tag metadata to every new receipt."""

    def __init__(
        self,
        path: str | Path,
        *,
        signing_key: bytes | None = None,
        require_signing: bool = False,
    ) -> None:
        super().__init__(
            path,
            signing_key=signing_key,
            require_signing=require_signing,
        )

    def append(
        self,
        *,
        actor: str,
        decision: str,
        subject_id: str,
        details: Mapping[str, Any],
        executor: str | None = None,
    ) -> Receipt:
        existing = self.read_all()
        previous = existing[-1] if existing else None
        chained_details = dict(details)
        chained_details["_chain_sequence"] = len(existing) + 1
        chained_details["_previous_integrity_tag"] = (
            previous.integrity_tag if previous else None
        )
        return super().append(
            actor=actor,
            decision=decision,
            subject_id=subject_id,
            details=chained_details,
            executor=executor,
        )

    def verify_chain(self) -> bool:
        """Verify record integrity and chain links for the complete log."""
        previous_tag: str | None = None
        for expected_sequence, receipt in enumerate(self.read_all(), start=1):
            if not self.verify(receipt):
                return False
            if receipt.details.get("_chain_sequence") != expected_sequence:
                return False
            if receipt.details.get("_previous_integrity_tag") != previous_tag:
                return False
            previous_tag = receipt.integrity_tag
        return True
