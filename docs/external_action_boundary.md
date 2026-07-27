# External Action Boundary

External providers are not trusted execution authorities. Calendar, notification, commerce, finance, supplier, fulfilment, and future device adapters may only be invoked by a bounded executor after the normal Event Protocol, Runtime, identity, Court, safety, and one-use authorization path has succeeded.

## Required sequence

```text
approved business intent
  -> Runtime-owned route
  -> Court authorization
  -> bounded executor
  -> durable external-operation preparation
  -> idempotent provider request
  -> provider confirmation or durable failure
  -> local record reconciliation
  -> canonical Receipt
```

## Laws

- An adapter is a provider boundary, not an authority boundary.
- A provider adapter must not be exposed directly to agents, models, dashboards, remote clients, or business organs.
- External writes require a durable `ExternalOperationJournal` entry before the provider call in production composition.
- Provider success must be reconciled to a local record before the operation is considered complete.
- Provider failure must be durably recorded and must not create a local success record.
- Idempotency keys bind retries to the original operation and must not be reused for different subjects or payloads.
- Credentials belong in local secret storage and must never enter intents, events, receipts, logs, examples, or repository files.
- A real adapter may replace an in-memory adapter only through the application composition boundary. Replacement does not bypass Runtime, Court, safety, executor, journal, or Receipt requirements.
- Replaying an event, receipt, or previously authorized intent must not repeat an external side effect.

## Current posture

The repository includes deterministic in-memory adapters for local development and tests. They model provider behaviour but do not contact external services. Any future production adapter remains disabled until its credential handling, idempotency, reconciliation, recovery, and outcome-verification contracts are reviewed.
