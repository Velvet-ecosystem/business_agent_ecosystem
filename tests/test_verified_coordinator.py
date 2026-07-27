from business_agents.contracts import ExecutorResult
from business_agents.gateway.principal_coordinator import PrincipalBusinessCoordinator
from business_agents.gateway.verified_coordinator import VerifiedBusinessCoordinator
from business_agents.identity import PresenceLevel, VerifiedPrincipal


class Receipts:
    def __init__(self) -> None:
        self.items = []

    def append(self, **kwargs):
        self.items.append(kwargs)


class Coordinator:
    def __init__(self) -> None:
        self.receipt_store = Receipts()
        self.last_context = None

    def run(self, agent, context, *, identity_verified):
        self.last_context = dict(context)
        return ExecutorResult("Demo", "completed", "receipt-1", {"job_id": "JOB-1"})


def principal() -> VerifiedPrincipal:
    return VerifiedPrincipal(
        principal_id="owner-1",
        display_name="Mister",
        role="owner",
        authentication_method="local",
        presence_level=PresenceLevel.PHYSICAL,
        session_id="session-1",
        verified_at=100.0,
    )


def test_fresh_principal_is_bound(monkeypatch) -> None:
    base = Coordinator()
    wrapper = VerifiedBusinessCoordinator(base, max_age_seconds=30)
    monkeypatch.setattr(VerifiedPrincipal, "is_fresh", lambda self, max_age_seconds: True)
    wrapper.run(object(), {}, principal=principal())
    assert base.last_context["_principal_id"] == "owner-1"
    assert base.receipt_store.items[-1]["decision"] == "actor-bound"


def test_stale_principal_is_rejected(monkeypatch) -> None:
    base = Coordinator()
    wrapper = VerifiedBusinessCoordinator(base, max_age_seconds=30)
    monkeypatch.setattr(VerifiedPrincipal, "is_fresh", lambda self, max_age_seconds: False)
    try:
        wrapper.run(object(), {}, principal=principal())
    except PermissionError as exc:
        assert str(exc) == "identity-stale"
    else:
        raise AssertionError("stale principal was accepted")


def test_compatibility_wrapper_binds_fresh_principal(monkeypatch) -> None:
    base = Coordinator()
    wrapper = PrincipalBusinessCoordinator(base, max_age_seconds=30)
    monkeypatch.setattr(VerifiedPrincipal, "is_fresh", lambda self, max_age_seconds: True)
    wrapper.run(object(), {}, principal=principal())
    assert base.last_context["_principal_id"] == "owner-1"
    assert base.last_context["_principal_session_id"] == "session-1"


def test_compatibility_wrapper_rejects_stale_principal(monkeypatch) -> None:
    base = Coordinator()
    wrapper = PrincipalBusinessCoordinator(base, max_age_seconds=30)
    monkeypatch.setattr(VerifiedPrincipal, "is_fresh", lambda self, max_age_seconds: False)
    try:
        wrapper.run(object(), {}, principal=principal())
    except PermissionError as exc:
        assert str(exc) == "identity-stale"
    else:
        raise AssertionError("compatibility wrapper accepted stale principal")
