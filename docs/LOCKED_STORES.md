# Locked Artifact Stores

Locked, legacy-compatible stores now exist for booking preparations, notification drafts, delivery records, and work-start records.

They live in `business_agents.locked_artifact_stores` and keep the same public methods used by the existing executors.

New writes use process locks, schema envelopes, flush, and `fsync`. Duplicate and idempotency checks remain under the same lock through append.

`business_agents.store_bundle.build_store_bundle()` creates the four stores from one data directory.

The next step is a small composition-root wiring change so the main application constructs this bundle by default.
