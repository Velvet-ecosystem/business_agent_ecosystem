import pytest

from business_agents.identity import PresenceLevel, VerifiedPrincipal


def test_verified_principal_details_and_freshness() -> None:
    principal = VerifiedPrincipal(
        principal_id="owner-1",
        display_name="Mister",
        role="owner",
        authentication_method="local",
        presence_level=PresenceLevel.PHYSICAL,
        session_id="session-1",
        verified_at=100.0,
    )
    assert principal.receipt_details()["principal_id"] == "owner-1"
    assert principal.is_fresh(max_age_seconds=30, clock=lambda: 120.0)
    assert not principal.is_fresh(max_age_seconds=30, clock=lambda: 131.0)


def test_verified_principal_rejects_empty_identity_fields() -> None:
    with pytest.raises(ValueError, match="principal_id must be a non-empty string"):
        VerifiedPrincipal(
            principal_id="",
            display_name="Mister",
            role="owner",
            authentication_method="local",
            presence_level=PresenceLevel.PHYSICAL,
            session_id="session-1",
            verified_at=100.0,
        )
