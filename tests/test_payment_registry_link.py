from business_agents.agents.payment_recording_agent import PaymentRecordingAgent
from business_agents.capability_registry import capability_for_identity
from tests.test_reported_amount_recording import make_context


def test_payment_proposal_matches_registered_identity() -> None:
    capability = capability_for_identity("payment-recording", "record-reported-payment")
    assert capability is not None
    proposal = PaymentRecordingAgent().propose(make_context())
    assert proposal.intent.route == capability.route
    assert proposal.intent.action == capability.action
