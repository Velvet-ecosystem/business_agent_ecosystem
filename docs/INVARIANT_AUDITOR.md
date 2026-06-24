# Lifecycle Invariant Auditor

`LifecycleInvariantAuditor` performs a read-only audit across the stored business lifecycle.

It checks for:

- estimates and schedule proposals referencing missing jobs
- booking preparations referencing missing or mismatched schedule proposals
- bookings referencing missing jobs or preparations
- scheduled, in-progress, or completed jobs without bookings
- multiple bookings for one job
- notification drafts referencing missing or mismatched bookings
- deliveries referencing missing or mismatched drafts
- multiple deliveries for one draft
- work-start records referencing missing or mismatched bookings
- in-progress or completed jobs without work-start records
- work-start records created before the job reaches in-progress
- multiple work-start records for one job
- provider-confirmed external operations still awaiting local reconciliation
- external operations claiming local records that do not exist

The auditor never mutates stored records.

Use:

```python
from pathlib import Path
from business_agents.audit_report import report_as_text, run_audit

report = run_audit(Path("data"))
print(report_as_text(report))
```

Machine-readable output is available through `report_as_dict()` and `report_as_json()`.

A clean report means no currently defined invariant violations were found. It does not replace receipt verification, provider reconciliation, or domain-specific review.
