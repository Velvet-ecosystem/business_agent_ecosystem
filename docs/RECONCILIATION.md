# Reconciliation Journal

Calendar booking and notification delivery can now record three external-write milestones: prepared, provider-confirmed, and locally-recorded.

A provider-confirmed operation without a local record is returned by `pending_reconciliation()`.

Use `business_agents.reconcile.attach(application, path)` after building the application. It replaces only the two provider-writing executors and gives both the same journal.

Retries reuse the original idempotency key, allowing the local record to be completed without creating a second external event or message.
