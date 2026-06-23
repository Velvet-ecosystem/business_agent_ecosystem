from business_agents.agents.inventory_agent import InventoryAgent
from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel
from business_agents.gateway.authority import CourtPolicy, intent_fingerprint


def inventory_proposal():
    return InventoryAgent().propose(
        {
            "sku": "FILTER-001",
            "location": "small-workshop",
            "on_hand": 2,
            "reorder_point": 8,
            "suggested_quantity": 12,
        }
    )


def test_authorization_ids_are_unique() -> None:
    court = CourtPolicy()
    proposal = inventory_proposal()

    first = court.evaluate(
        proposal, identity_verified=True, safety_passed=True
    )
    second = court.evaluate(
        proposal, identity_verified=True, safety_passed=True
    )

    assert first.authorization_id != second.authorization_id
    assert first.intent_fingerprint == second.intent_fingerprint


def test_authorization_is_bound_to_exact_intent() -> None:
    court = CourtPolicy()
    proposal = inventory_proposal()
    decision = court.evaluate(
        proposal, identity_verified=True, safety_passed=True
    )
    altered = BusinessIntent(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters={**dict(proposal.intent.parameters), "suggested_quantity": 13},
    )

    assert decision.authorization_id is not None
    assert court.consume_authorization(decision.authorization_id, altered) is False


def test_authorization_is_bound_to_risk_and_approval_mode() -> None:
    court = CourtPolicy()
    proposal = inventory_proposal()
    decision = court.evaluate(
        proposal, identity_verified=True, safety_passed=True
    )
    altered = BusinessIntent(
        route=proposal.intent.route,
        action=proposal.intent.action,
        subject_id=proposal.intent.subject_id,
        parameters=proposal.intent.parameters,
        risk_level=RiskLevel.HIGH,
        approval_mode=ApprovalMode.HUMAN,
    )

    assert decision.authorization_id is not None
    assert court.consume_authorization(decision.authorization_id, altered) is False


def test_authorization_can_only_be_consumed_once() -> None:
    court = CourtPolicy()
    proposal = inventory_proposal()
    decision = court.evaluate(
        proposal, identity_verified=True, safety_passed=True
    )

    assert decision.authorization_id is not None
    assert court.consume_authorization(
        decision.authorization_id, proposal.intent
    ) is True
    assert court.consume_authorization(
        decision.authorization_id, proposal.intent
    ) is False


def test_fingerprint_is_stable_for_parameter_order() -> None:
    first = BusinessIntent(
        route="internal-task",
        action="create-restock-review",
        subject_id="small-workshop",
        parameters={"sku": "FILTER-001", "suggested_quantity": 12},
    )
    second = BusinessIntent(
        route="internal-task",
        action="create-restock-review",
        subject_id="small-workshop",
        parameters={"suggested_quantity": 12, "sku": "FILTER-001"},
    )

    assert intent_fingerprint(first) == intent_fingerprint(second)
