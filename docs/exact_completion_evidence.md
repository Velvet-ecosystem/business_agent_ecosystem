# Exact Completion Evidence

A job may move from `in-progress` to `completed` only through the `job-completion` route.

The completion request must reference the exact durable completion-evidence record already bound to the same job. The executor re-reads both the job and evidence at execution time and fails closed when:

- the job is no longer `in-progress`
- the evidence record does not exist
- the evidence belongs to another job
- the referenced evidence is not the record bound to that job
- strong-human authorization metadata is missing or invalid

A successful transition emits a receipt containing the evidence ID, verified completer identity from the evidence record, lifecycle transition, and authorization metadata.

This slice does not create invoices, send customer communications, or trigger payment activity.
