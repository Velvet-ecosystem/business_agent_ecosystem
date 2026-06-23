from business_agents.contracts import ExecutorResult
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


def principal(verified_at: float) -> VerifiedPrincipal:
    return VerifiedPrincipal(
        principal_id="owner-1",
        display_name="Mister",
        role="owner",
        authentication_method="local",
        presence_level=PresenceLevel.PHYSICAL,
        session_id="session-1",
        verified_at=verified_at,
    )


def test_fresh_principal_is_bound(monkeypatch) -> None:
    base = Coordinator()
    wrapper = VerifiedBusinessCoordinator(base, max_age_seconds=30)
    monkeypatch.setattr("business_agents.identity.time.time", lambda: 120.0)
    wrapper.run(object(), {}, principal=principal(100.0))
    assert base.last_context["_principal_id"] == "owner-1"
    assert base.receipt_store.items[-1]["decision"] == "actor-bound"


def test_stale_principal_is_rejected(monkeypatch) -> None:
    base = Coordinator()
    wrapper = VerifiedBusinessCoordinator(base, max_age_seconds=30)
    monkeypatch.setattr("business_agents.identity.time.time", lambda: 140.0)
    try:
        wrapper.run(object(), {}, principal=principal(100.0))
    except PermissionError as exc:
        assert str(exc) == "identity-stale"
    else:
        raise AssertionError("stale principal was accepted")
