# Compatibility-Safe Store Migration

The job and booking stores now use the shared locked JSONL foundation.

They preserve their existing public APIs and read both formats:

- legacy raw JSON objects
- versioned schema envelopes

New writes use schema envelopes, process locks, flush, and `fsync`. Existing files are not rewritten in place.

The migrated stores are:

- `JsonlJobStore` using schema `job-event`
- `JsonlBookingStore` using schema `booking-record`

Job creation and transitions now hold one lock across read, validation, and append. Booking creation holds one lock across idempotency checks, duplicate checks, and append.

The compatibility layer is `CompatibleLockedJsonlFile`. Remaining stores should migrate through the same layer before legacy raw-line support is retired.
