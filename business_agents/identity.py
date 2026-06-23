"""Durable identity contract for authenticated business actors."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class PresenceLevel(str, Enum):
    REMOTE = "remote"
    LOCAL = "local"
    PHYSICAL = "physical"


@dataclass(frozen=True)
class VerifiedPrincipal:
    principal_id: str
    display_name: str
    role: str
    authentication_method: str
    presence_level: PresenceLevel
    session_id: str
    verified_at: float

    def __post_init__(self) -> None:
        for name, value in (
            ("principal_id", self.principal_id),
            ("display_name", self.display_name),
            ("role", self.role),
            ("authentication_method", self.authentication_method),
            ("session_id", self.session_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.verified_at <= 0:
            raise ValueError("verified_at must be positive")

    def is_fresh(self, *, max_age_seconds: float, clock: Callable[[], float] = time.time) -> bool:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        age = clock() - self.verified_at
        return 0 <= age <= max_age_seconds

    def receipt_details(self) -> dict[str, object]:
        return {
            "principal_id": self.principal_id,
            "principal_display_name": self.display_name,
            "principal_role": self.role,
            "authentication_method": self.authentication_method,
            "presence_level": self.presence_level.value,
            "session_id": self.session_id,
            "verified_at": self.verified_at,
        }


def legacy_verified_principal(*, clock: Callable[[], float] = time.time) -> VerifiedPrincipal:
    """Compatibility identity for old boolean callers. Not for production use."""

    return VerifiedPrincipal(
        principal_id="legacy:boolean-verified",
        display_name="Legacy Verified Caller",
        role="legacy-compatibility",
        authentication_method="legacy-boolean",
        presence_level=PresenceLevel.REMOTE,
        session_id="legacy-session",
        verified_at=clock(),
    )
