import pytest

from business_agents.bound_artifact_scope import BoundArtifactScope


def test_exact_binding_matches():
    record = BoundArtifactScope(
        artifact_id="artifact-001",
        artifact_digest="a" * 64,
        route="example.route",
        action="example-action",
        subject_id="artifact-001",
        handler_id="handler-001",
    )
    assert record.matches(
        artifact_id="artifact-001",
        artifact_digest="a" * 64,
        route="example.route",
        action="example-action",
        subject_id="artifact-001",
        handler_id="handler-001",
    )


def test_digest_change_fails_match():
    record = BoundArtifactScope(
        artifact_id="artifact-001",
        artifact_digest="a" * 64,
        route="example.route",
        action="example-action",
        subject_id="artifact-001",
        handler_id="handler-001",
    )
    assert not record.matches(
        artifact_id="artifact-001",
        artifact_digest="b" * 64,
        route="example.route",
        action="example-action",
        subject_id="artifact-001",
        handler_id="handler-001",
    )


def test_subject_must_match_artifact():
    with pytest.raises(ValueError, match="subject_id"):
        BoundArtifactScope(
            artifact_id="artifact-001",
            artifact_digest="a" * 64,
            route="example.route",
            action="example-action",
            subject_id="artifact-002",
            handler_id="handler-001",
        )
