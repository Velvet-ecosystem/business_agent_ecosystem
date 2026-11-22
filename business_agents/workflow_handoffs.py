"""Pure, read-only inter-department workflow contracts.

These structures only plan and verify artifact-reference handoffs. They never
invoke a model, tool, Court, Runtime, or business executor, and convey no grant.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _require_name(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_names(values: tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    for value in values:
        _require_name(value, name)
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates")


@dataclass(frozen=True)
class WorkflowStage:
    """A department's expected output, not an execution instruction."""

    stage_id: str
    department: str
    output_kind: str
    needs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("stage_id", "department", "output_kind"):
            _require_name(getattr(self, name), name)
        _require_names(self.needs, "needs")
        if self.stage_id in self.needs:
            raise ValueError("a stage cannot depend on itself")


@dataclass(frozen=True)
class WorkflowArtifactRef:
    """A run-bound digest reference, never raw client data or a credential."""

    workflow_id: str
    stage_id: str
    artifact_id: str
    kind: str
    sha256: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("workflow_id", "stage_id", "artifact_id", "kind"):
            _require_name(getattr(self, name), name)
        if not isinstance(self.sha256, str) or not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must be a lowercase 64-character hex digest")
        _require_names(self.evidence_refs, "evidence_refs")


@dataclass(frozen=True)
class WorkflowHandoff:
    """Exact artifact references offered to one department; no authority."""

    workflow_id: str
    target_stage: str
    department: str
    inputs: tuple[WorkflowArtifactRef, ...]


class WorkflowPlan:
    """Validates a DAG and deterministic, non-executing handoff readiness."""

    def __init__(self, workflow_id: str, stages: tuple[WorkflowStage, ...]) -> None:
        _require_name(workflow_id, "workflow_id")
        self.workflow_id = workflow_id
        if not isinstance(stages, tuple) or not stages:
            raise ValueError("stages must be a non-empty tuple")
        if any(not isinstance(stage, WorkflowStage) for stage in stages):
            raise ValueError("stages must contain WorkflowStage entries")
        self.stages = stages
        self._by_id = {stage.stage_id: stage for stage in stages}
        if len(self._by_id) != len(stages):
            raise ValueError("stage IDs must be unique")
        for stage in stages:
            if any(dependency not in self._by_id for dependency in stage.needs):
                raise ValueError("all dependencies must refer to known stages")

        visited: set[str] = set()
        active: set[str] = set()

        def visit(stage_id: str) -> None:
            if stage_id in active:
                raise ValueError("workflow dependencies must not contain cycles")
            if stage_id in visited:
                return
            active.add(stage_id)
            for dependency in self._by_id[stage_id].needs:
                visit(dependency)
            active.remove(stage_id)
            visited.add(stage_id)

        for stage in stages:
            visit(stage.stage_id)

    def _check_completed(self, completed: Mapping[str, WorkflowArtifactRef]) -> None:
        if not isinstance(completed, Mapping):
            raise ValueError("completed must be a mapping of stage IDs to artifact refs")
        for stage_id, artifact in completed.items():
            if stage_id not in self._by_id or not isinstance(artifact, WorkflowArtifactRef):
                raise ValueError("unknown stage or invalid artifact")
            stage = self._by_id[stage_id]
            if (artifact.workflow_id != self.workflow_id
                    or artifact.stage_id != stage_id or artifact.kind != stage.output_kind):
                raise ValueError("artifact belongs to a different stage or output kind")
            if not all(dependency in completed for dependency in stage.needs):
                raise ValueError("completed stage is missing a required predecessor")

    def ready_stages(self, completed: Mapping[str, WorkflowArtifactRef]) -> tuple[WorkflowStage, ...]:
        """Return uncompleted stages whose exact dependencies are all present."""
        self._check_completed(completed)
        return tuple(
            stage for stage in self.stages
            if stage.stage_id not in completed
            and all(dependency in completed for dependency in stage.needs)
        )

    def make_handoff(self, target_stage: str, completed: Mapping[str, WorkflowArtifactRef]) -> WorkflowHandoff:
        """Produce a reference-only snapshot for a currently ready stage."""
        _require_name(target_stage, "target_stage")
        ready = {stage.stage_id: stage for stage in self.ready_stages(completed)}
        if target_stage not in ready:
            raise ValueError("target stage is not ready or is already complete")
        stage = ready[target_stage]
        return WorkflowHandoff(
            workflow_id=self.workflow_id,
            target_stage=stage.stage_id,
            department=stage.department,
            inputs=tuple(completed[dependency] for dependency in stage.needs),
        )

    def validate_handoff(self, handoff: WorkflowHandoff, completed: Mapping[str, WorkflowArtifactRef]) -> None:
        """Reject a handoff if its parent artifact refs have changed."""
        if not isinstance(handoff, WorkflowHandoff):
            raise ValueError("handoff must be a WorkflowHandoff")
        if handoff.workflow_id != self.workflow_id or self.make_handoff(handoff.target_stage, completed) != handoff:
            raise ValueError("handoff reference drift")

    def accept_artifact(
        self, completed: Mapping[str, WorkflowArtifactRef], artifact: WorkflowArtifactRef
    ) -> dict[str, WorkflowArtifactRef]:
        """Return a new completed mapping; no persistent state or effects."""
        if not isinstance(artifact, WorkflowArtifactRef):
            raise ValueError("artifact must be a WorkflowArtifactRef")
        if artifact.workflow_id != self.workflow_id:
            raise ValueError("artifact belongs to another workflow")
        if artifact.stage_id not in {stage.stage_id for stage in self.ready_stages(completed)}:
            raise ValueError("artifact stage is not ready or was already completed")
        if artifact.kind != self._by_id[artifact.stage_id].output_kind:
            raise ValueError("artifact kind does not match required output")
        return {**completed, artifact.stage_id: artifact}


def example_sourcing_plan(workflow_id: str = "synthetic-demo-001") -> WorkflowPlan:
    """Synthetic client -> distributor -> manufacturer -> proposal workflow."""
    return WorkflowPlan(workflow_id, (
        WorkflowStage("intake", "customer-intake", "client-requirements"),
        WorkflowStage("client-research", "research", "client-research-brief", ("intake",)),
        WorkflowStage("distributor-research", "sourcing", "distributor-shortlist", ("client-research",)),
        WorkflowStage("manufacturer-check", "due-diligence", "manufacturer-evidence", ("distributor-research",)),
        WorkflowStage("commercial-comparison", "commercial", "landed-cost-comparison", ("manufacturer-check",)),
        WorkflowStage("proposal-preparation", "sales", "internal-proposal-draft", ("commercial-comparison",)),
        WorkflowStage("review", "quality-review", "human-review-package", ("proposal-preparation",)),
    ))
