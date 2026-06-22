from business_agents.contracts import AgentProposal, BusinessIntent
from business_agents.gateway.authority import CourtPolicy


def make_proposal() -> AgentProposal:
    return AgentProposal(
        agent_name="Inventory Agent",
        intent=BusinessIntent(
            route="inventory",
            action="recommend-restock",
            subject_id="warehouse-main",
            parameters={"sku": "FILTER-001", "quantity": 12},
        ),
        rationale="Observed stock is below the configured threshold.",
        confidence=0.91,
    )


def test_agent_proposal_never_grants_authority() -> None:
    proposal = make_proposal()
    assert proposal.authority_granted is False


def test_court_fails_closed_without_identity() -> None:
    decision = CourtPolicy().evaluate(
        make_proposal(), identity_verified=False, safety_passed=True
    )
    assert decision.approved is False
    assert decision.authorization_id is None


def test_court_fails_closed_when_safety_fails() -> None:
    decision = CourtPolicy().evaluate(
        make_proposal(), identity_verified=True, safety_passed=False
    )
    assert decision.approved is False
    assert decision.authorization_id is None


def test_court_approves_only_after_both_checks() -> None:
    decision = CourtPolicy().evaluate(
        make_proposal(), identity_verified=True, safety_passed=True
    )
    assert decision.approved is True
    assert decision.authorization_id is not None
