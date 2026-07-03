"""Pure immutable binding between a stored artifact and an exact operation scope."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoundArtifactScope:
    artifact_id: str
    artifact_digest: str
    route: str
    action: str
    subject_id: str
    handler_id: str

    def __post_init__(self) -> None:
        for name in (
            "artifact_id",
            "artifact_digest",
            "route",
            "action",
            "subject_id",
            "handler_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.artifact_digest) != 64 or any(
            character not in "0123456789abcdef" for character in self.artifact_digest
        ):
            raise ValueError("artifact_digest must be a lowercase SHA-256 hex digest")
        if self.subject_id != self.artifact_id:
            raise ValueError("subject_id must match artifact_id")

    def matches(
        self,
        *,
        artifact_id: str,
        artifact_digest: str,
        route: str,
        action: str,
        subject_id: str,
        handler_id: str,
    ) -> bool:
        return (
            self.artifact_id == artifact_id
            and self.artifact_digest == artifact_digest
            and self.route == route
            and self.action == action
            and self.subject_id == subject_id
            and self.handler_id == handler_id
        )
