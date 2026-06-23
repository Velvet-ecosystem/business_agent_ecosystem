"""Durable internal customer-notification drafts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class NotificationDraft:
    draft_id: str
    job_id: str
    booking_id: str
    channel: str
    recipient: str
    subject: str
    body: str

    def __post_init__(self) -> None:
        for name, value in (
            ("draft_id", self.draft_id),
            ("job_id", self.job_id),
            ("booking_id", self.booking_id),
            ("channel", self.channel),
            ("recipient", self.recipient),
            ("subject", self.subject),
            ("body", self.body),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.channel != "email":
            raise ValueError("only email drafts are currently supported")
        if len(self.subject) > 200:
            raise ValueError("subject is too long")
        if len(self.body) > 10000:
            raise ValueError("body is too long")


class JsonlNotificationDraftStore:
    """Append-only store for unsent customer-notification drafts."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, draft: NotificationDraft) -> NotificationDraft:
        if self.get(draft.draft_id) is not None:
            raise ValueError(f"notification draft already exists: {draft.draft_id}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(draft), sort_keys=True, ensure_ascii=False) + "\n")
        return draft

    def get(self, draft_id: str) -> NotificationDraft | None:
        if not self.path.exists():
            return None
        found: NotificationDraft | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid notification draft at line {line_number}") from exc
                if payload.get("draft_id") == draft_id:
                    found = NotificationDraft(
                        draft_id=str(payload["draft_id"]),
                        job_id=str(payload["job_id"]),
                        booking_id=str(payload["booking_id"]),
                        channel=str(payload["channel"]),
                        recipient=str(payload["recipient"]),
                        subject=str(payload["subject"]),
                        body=str(payload["body"]),
                    )
        return found
