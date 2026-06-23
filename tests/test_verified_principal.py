from business_agents.identity import PresenceLevel, VerifiedPrincipal, legacy_verified_principal


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


def test_legacy_identity_is_marked() -> None:
    principal = legacy_verified_principal(clock=lambda: 100.0)
    assert principal.authentication_method == "legacy-boolean"
    assert principal.role == "legacy-compatibility"
