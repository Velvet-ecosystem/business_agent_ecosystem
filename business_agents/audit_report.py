"""Human and machine-readable formatting for lifecycle audit reports."""

from __future__ import annotations

import json
from pathlib import Path

from business_agents.invariant_auditor import AuditReport, LifecycleInvariantAuditor


def run_audit(data_dir: Path) -> AuditReport:
    return LifecycleInvariantAuditor(data_dir).audit()


def report_as_dict(report: AuditReport) -> dict[str, object]:
    return {
        "clean": report.clean,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "findings": [
            {
                "code": item.code,
                "severity": item.severity,
                "subject_id": item.subject_id,
                "message": item.message,
                "related_ids": list(item.related_ids),
            }
            for item in report.findings
        ],
    }


def report_as_json(report: AuditReport) -> str:
    return json.dumps(report_as_dict(report), indent=2, sort_keys=True)


def report_as_text(report: AuditReport) -> str:
    if report.clean:
        return "Lifecycle invariant audit: clean"
    lines = [
        f"Lifecycle invariant audit: {report.error_count} errors, "
        f"{report.warning_count} warnings"
    ]
    for item in report.findings:
        related = f" [{', '.join(item.related_ids)}]" if item.related_ids else ""
        lines.append(
            f"{item.severity.upper()} {item.code} {item.subject_id}: "
            f"{item.message}{related}"
        )
    return "\n".join(lines)
