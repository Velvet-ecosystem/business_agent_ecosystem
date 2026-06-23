# Foundation Hardening

Before the business lifecycle expands beyond work start, the repository is consolidating its shared foundations.

## Application composition root

`business_agents.application.build_application()` now creates one coherent application graph from a single data directory.

It assembles:

- Court policy
- route-aware safety-gate registry
- executor registry
- all lifecycle stores
- calendar adapter
- notification-delivery adapter
- business coordinator

Application startup fails if safety routes and executor routes do not match. This prevents an executor from being enabled without its safety gate or a safety route from existing without an executor.

Production code should obtain stores and the coordinator from this composition root rather than manually assembling separate object graphs.

## Locked versioned JSONL foundation

`business_agents.storage.LockedJsonlFile` provides:

- separate process lock files
- POSIX and Windows locking
- schema and version envelopes
- corruption detection with line locations
- locked uniqueness checks
- flush and `fsync` after appends

Existing prototype stores remain readable in their current formats. They will be migrated deliberately rather than silently rewritten. New migrations must preserve append-only history and include compatibility tests.

## Remaining foundation sequence

1. migrate stores onto the shared locked primitive
2. add durable verified-principal identity
3. add external-operation reconciliation journal
4. add cross-record integrity auditor
5. require CI checks on every main-branch change
6. resume completion and invoicing work
