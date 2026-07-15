"""Build canonical procurement BusinessIntents from approved lineage packages."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from business_agents.contracts import ApprovalMode, BusinessIntent, RiskLevel

PROCUREMENT_ROUTE = "procurement.order"
PROCUREMENT_ACTION = "place-bounded-order"
REQUIRED_LINEAGE_FIELDS = frozenset(
    {
        "approval_request_id",
        "decision_id",
        "artifact_id",
        "artifact_digest",
        "route",
        "action",
        "subject_id",
        "risk_level",
        "approval_mode",
        "bounded_to_exact_artifact_digest",
    }
)


def build_procurement_intent(
    lineage_package: Mapping[str, Any], *, handler_id: str
) -> BusinessIntent:
    validate_procurement_lineage(lineage_package)
    if not isinstance(handler_id, str) or not handler_id.strip():
        raise ValueError("handler_id must be a non-empty string")

    artifact_id = str(lineage_package["artifact_id"])
    parameters = {
        "artifact_id": artifact_id,
        "artifact_digest": str(lineage_package["artifact_digest"]),
        "handler_id": handler_id,
        "approval_request_id": str(lineage_package["approval_request_id"]),
        "decision_id": str(lineage_package["decision_id"]),
        "lineage_route": str(lineage_package["route"]),
        "lineage_action": str(lineage_package["action"]),
        "lineage_subject_id": str(lineage_package["subject_id"]),
    }
    return BusinessIntent(
        route=PROCUREMENT_ROUTE,
        action=PROCUREMENT_ACTION,
        subject_id=artifact_id,
        parameters=parameters,
        risk_level=RiskLevel.HIGH,
        approval_mode=ApprovalMode.STRONG_HUMAN,
    )


def validate_procurement_lineage(lineage_package: Mapping[str, Any]) -> None:
    if not isinstance(lineage_package, Mapping):
        raise ValueError("lineage_package must be a mapping")
    missing = sorted(REQUIRED_LINEAGE_FIELDS.difference(lineage_package))
    if missing:
        raise ValueError(f"lineage_package missing required fields: {', '.join(missing)}")

    for name in REQUIRED_LINEAGE_FIELDS - {"bounded_to_exact_artifact_digest"}:
        value = lineage_package[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    artifact_id = str(lineage_package["artifact_id"])
    artifact_digest = str(lineage_package["artifact_digest"])
    if len(artifact_digest) != 64 or any(
        character not in "0123456789abcdef" for character in artifact_digest
    ):
        raise ValueError("artifact_digest must be a lowercase SHA-256 hex digest")
    if lineage_package["subject_id"] != artifact_id:
        raise ValueError("lineage subject_id must match artifact_id")
    if lineage_package["route"] != PROCUREMENT_ROUTE:
        raise ValueError("lineage route must match procurement route")
    if lineage_package["action"] != PROCUREMENT_ACTION:
        raise ValueError("lineage action must match procurement action")
    if lineage_package["risk_level"] != RiskLevel.HIGH.value:
        raise ValueError("lineage risk_level must be high")
    if lineage_package["approval_mode"] != ApprovalMode.STRONG_HUMAN.value:
        raise ValueError("lineage approval_mode must be strong-human")
    if lineage_package["bounded_to_exact_artifact_digest"] is not True:
        raise ValueError("lineage must be bounded to exact artifact digest")
