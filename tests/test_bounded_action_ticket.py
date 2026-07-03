from datetime import datetime, timedelta, timezone

import pytest

from business_agents.bound_artifact_scope import BoundArtifactScope
from business_agents.bounded_action_ticket import BoundedActionTicket, BoundedActionTicketStatus


def make_binding() -> BoundArtifactScope:
    return BoundArtifactScope(
        artifact_id="artifact-001",
        artifact_digest="a" * 64,
        route="example.route",
        action="example-action",
        subject_id="artifact-001",
        handler_id="handler-001",
    )


def make_ticket(**changes):
    start = datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)
    values = {
        "ticket_id": "ticket-001",
        "approval_request_id": "approval-001",
        "decision_id": "decision-001",
        "binding": make_binding(),
        "issued_by": "Court",
        "issued_at": start,
        "expires_at": start + timedelta(minutes=5),
    }
    values.update(changes)
    return BoundedActionTicket(**values)


def test_ticket_is_live_only_inside_window():
    ticket = make_ticket()
    assert ticket.is_live(ticket.issued_at)
    assert ticket.is_live(ticket.issued_at + timedelta(minutes=1))
    assert not ticket.is_live(ticket.expires_at)


def test_ticket_matches_exact_binding_only():
    ticket = make_ticket()
    assert ticket.matches(
        artifact_id="artifact-001",
        artifact_digest="a" * 64,
        route="example.route",
        action="example-action",
        subject_id="artifact-001",
        handler_id="handler-001",
    )
    assert not ticket.matches(
        artifact_id="artifact-001",
        artifact_digest="b" * 64,
        route="example.route",
        action="example-action",
        subject_id="artifact-001",
        handler_id="handler-001",
    )


def test_ticket_requires_binding():
    with pytest.raises(ValueError, match="BoundArtifactScope"):
        make_ticket(binding="invalid")


def test_ticket_must_be_single_use():
    with pytest.raises(ValueError, match="single-use"):
        make_ticket(max_uses=2)


def test_ticket_requires_expected_issuer():
    with pytest.raises(ValueError, match="issued by Court"):
        make_ticket(issued_by="agent")


def test_consumed_ticket_is_not_live():
    ticket = make_ticket(status=BoundedActionTicketStatus.CONSUMED, uses=1)
    assert not ticket.is_live(ticket.issued_at + timedelta(minutes=1))


def test_active_ticket_cannot_already_be_used():
    with pytest.raises(ValueError, match="active ticket"):
        make_ticket(uses=1)


def test_ticket_requires_timezone_aware_dates():
    with pytest.raises(ValueError, match="issued_at"):
        make_ticket(issued_at=datetime(2026, 7, 2, 12, 0))


def test_ticket_requires_positive_lifetime():
    start = datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="expires_at"):
        make_ticket(issued_at=start, expires_at=start)
