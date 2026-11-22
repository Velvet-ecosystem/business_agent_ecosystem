import pytest

from business_agents.workflow_handoffs import (
    WorkflowArtifactRef,
    WorkflowPlan,
    WorkflowStage,
    example_sourcing_plan,
)


DIGEST = 'a' * 64


def ref(stage_id: str, kind: str, digest: str = DIGEST) -> WorkflowArtifactRef:
    return WorkflowArtifactRef('synthetic-demo-001', stage_id, f'artifact-{stage_id}', kind, digest, ('source-ref-1',))


def test_sourcing_pipeline_requires_previous_department() -> None:
    plan = example_sourcing_plan()
    assert [s.stage_id for s in plan.ready_stages({})] == ['intake']
    first = ref('intake', 'client-requirements')
    completed = plan.accept_artifact({}, first)
    handoff = plan.make_handoff('client-research', completed)
    assert handoff.department == 'research'
    assert handoff.inputs == (first,)
    assert [s.stage_id for s in plan.ready_stages(completed)] == ['client-research']
    with pytest.raises(ValueError):
        plan.make_handoff('manufacturer-check', completed)


def test_handoff_rejects_reference_drift() -> None:
    plan = example_sourcing_plan()
    completed = plan.accept_artifact({}, ref('intake', 'client-requirements'))
    old = plan.make_handoff('client-research', completed)
    updated = {'intake': ref('intake', 'client-requirements', 'b' * 64)}
    with pytest.raises(ValueError, match='drift'):
        plan.validate_handoff(old, updated)


def test_accept_rejects_wrong_kind_and_repeat() -> None:
    plan = example_sourcing_plan()
    with pytest.raises(ValueError, match='kind'):
        plan.accept_artifact({}, ref('intake', 'customer-message'))
    completed = plan.accept_artifact({}, ref('intake', 'client-requirements'))
    with pytest.raises(ValueError):
        plan.accept_artifact(completed, ref('intake', 'client-requirements'))


def test_rejects_broken_and_cyclic_graphs() -> None:
    with pytest.raises(ValueError, match='known'):
        WorkflowPlan('synthetic-demo-001', (WorkflowStage('x', 'dept', 'out', ('missing',)),))
    with pytest.raises(ValueError, match='cycles'):
        WorkflowPlan('synthetic-demo-001', (WorkflowStage('a', 'dept', 'out', ('b',)), WorkflowStage('b', 'dept', 'out', ('a',))))
    with pytest.raises(ValueError, match='unique'):
        WorkflowPlan('synthetic-demo-001', (WorkflowStage('a', 'dept', 'out'), WorkflowStage('a', 'dept', 'out')))


def test_rejects_forged_completed_stage() -> None:
    plan = example_sourcing_plan()
    with pytest.raises(ValueError, match='missing'):
        plan.ready_stages({'client-research': ref('client-research', 'client-research-brief')})
    with pytest.raises(ValueError, match='different'):
        plan.ready_stages({'intake': ref('elsewhere', 'client-requirements')})
    with pytest.raises(ValueError, match='known'):
        plan.ready_stages({'unknown': ref('unknown', 'client-requirements')})


def test_rejects_invalid_artifact_digests() -> None:
    with pytest.raises(ValueError, match='sha256'):
        ref('intake', 'client-requirements', 'not-a-digest')
    with pytest.raises(ValueError, match='sha256'):
        ref('intake', 'client-requirements', 'A' * 64)


def test_parallel_stages_join_when_both_dependencies_completed() -> None:
    plan = WorkflowPlan('synthetic-demo-001', (
        WorkflowStage('intake', 'intake', 'req'),
        WorkflowStage('client', 'research', 'client-note', ('intake',)),
        WorkflowStage('supplier', 'research', 'supplier-note', ('intake',)),
        WorkflowStage('compare', 'sales', 'comparison', ('client', 'supplier')),
    ))
    completed = plan.accept_artifact({}, ref('intake', 'req'))
    assert {s.stage_id for s in plan.ready_stages(completed)} == {'client', 'supplier'}
    completed = plan.accept_artifact(completed, ref('client', 'client-note'))
    with pytest.raises(ValueError):
        plan.make_handoff('compare', completed)
    completed = plan.accept_artifact(completed, ref('supplier', 'supplier-note'))
    handoff = plan.make_handoff('compare', completed)
    assert [item.stage_id for item in handoff.inputs] == ['client', 'supplier']


def test_no_implicit_external_tools_or_execution() -> None:
    plan = example_sourcing_plan()
    assert all(not hasattr(plan, item) for item in ('execute', 'authorize', 'send', 'purchase'))
    assert not hasattr(plan.make_handoff('intake', {}), 'authorization')


def test_refuses_cross_client_artifacts_and_handoffs() -> None:
    a = example_sourcing_plan('synthetic-demo-001')
    b = example_sourcing_plan('synthetic-demo-002')
    proof = ref('intake', 'client-requirements')
    completed = a.accept_artifact({}, proof)
    with pytest.raises(ValueError, match='different'):
        b.ready_stages(completed)
    with pytest.raises(ValueError, match='another workflow'):
        b.accept_artifact({}, proof)
    with pytest.raises(ValueError, match='drift'):
        b.validate_handoff(a.make_handoff('client-research', completed), {'intake': WorkflowArtifactRef('synthetic-demo-002', 'intake', 'artifact-intake', 'client-requirements', DIGEST)})
