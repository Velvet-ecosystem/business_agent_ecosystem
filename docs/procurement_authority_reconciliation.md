# Procurement Authority Reconciliation

## Decision

The current `CourtPolicy` and `BusinessCoordinator` implementation is the canonical **internal business-domain compatibility path** for procurement and the other working slices in this repository.

It must remain subordinate to the public Velvet constitutional architecture:

```text
Event Protocol
  -> Runtime
  -> business safety and identity validation
  -> Court
  -> bounded executor
  -> observed result
  -> canonical Receipt
```

Procurement must extend `business_agents.gateway.authority.CourtPolicy` and `business_agents.gateway.coordinator.BusinessCoordinator` until direct Runtime integration is complete. It must not introduce a second issuer, parallel authorization ledger, independent Runtime, or executor bypass.

## Existing Court properties

`CourtPolicy` already provides:

- fail-closed identity and safety requirements
- deterministic SHA-256 fingerprinting over the complete `BusinessIntent`
- route, action, subject, parameters, risk, and approval-mode binding
- short-lived grants
- optional principal and session binding
- one-use consumption
- replay rejection
- expiry rejection
- intent-mutation rejection
- actor-drift rejection

`BusinessCoordinator` currently provides the internal business execution order:

```text
bounded organ proposal
  -> safety evaluation
  -> Court evaluation
  -> authorization or denial Receipt
  -> executor lookup
  -> one-use grant consumption
  -> executor invocation
```

This coordinator is not the ecosystem Runtime. It is a business-domain composition layer and migration bridge that must remain compatible with Runtime routes, state, Event Protocol contracts, Court policy, and canonical Receipts.

Denied, missing, invalid, expired, stale, or unavailable paths fail closed and produce Receipts where appropriate.

## Procurement preparation boundary

The procurement slice provides:

```text
requirement
  -> researched supplier candidates
  -> comparison
  -> prepared purchase package
  -> immutable prepared artifact and canonical digest
  -> exact artifact review request
  -> explicit human decision
  -> decision-aware review state
  -> lineage package carrying artifact ID and digest
  -> immutable route/action/subject/handler binding
  -> inert bounded record
```

This boundary grants no purchasing authority and performs no external action.

## Reconciliation model

The immutable procurement artifact becomes part of the canonical `BusinessIntent.parameters` before Court evaluation:

```text
approved procurement lineage
  -> construct one BusinessIntent
       route
       action
       subject_id = artifact_id
       parameters.artifact_id
       parameters.artifact_digest
       parameters.handler_id
       parameters.approval_request_id
       parameters.decision_id
  -> Event Protocol-compatible proposal
  -> Runtime route and state validation
  -> procurement safety evaluation
  -> CourtPolicy evaluation
  -> short-lived intent grant
  -> internal coordinator consumption
  -> one registered procurement executor
  -> observed dry-run result
  -> canonical Receipt
```

Because `intent_fingerprint()` includes the complete parameters mapping, any change to supplier, part, quantity, price, currency, destination, artifact digest, handler, approval request, or decision lineage produces a different fingerprint and invalidates the original grant.

## Relationship to the bounded record

The current bounded record is an inert contract and test fixture, not a second authorization system.

Preferred implementation:

1. Treat the bounded record as a typed procurement payload embedded in canonical `BusinessIntent.parameters`.
2. Keep Court as the sole business-domain issuer and one-use grant store during the compatibility phase.
3. Route future production execution through Runtime without creating a parallel coordinator.
4. Emit Event Protocol-compatible lifecycle and result events.
5. Produce canonical Receipts for authorization, denial, attempt, result, and discrepancy.

A future refactor may generalize authorization contracts for all domains, but procurement must never persist or consume a separate grant beside the canonical Court path.

## Required work before external execution

1. Add negative integration tests for denial, missing artifacts, changed route, action, handler, digest, principal, state, and expiry.
2. Define the exact procurement `BusinessIntent`, Event Protocol, and Runtime route contracts.
3. Bind the final handler through the executor registry and Runtime capability declaration.
4. Re-read the immutable artifact immediately before execution.
5. Verify the artifact digest and all commercial fields against the approved intent.
6. Add supplier-response and financial-result verification.
7. Write canonical Receipts for authorization, attempted execution, verified outcome, and discrepancies.
8. Add explicit revocation, cancellation, recovery, and idempotency behaviour.
9. Preserve dry-run and no-external-effect tests after any connector is introduced.

## Deferred capabilities

The following remain intentionally absent:

- supplier contact
- payment credential access
- order placement
- refunds or cancellation
- financial transfer
- stock mutation
- procurement-specific Court issuer
- procurement-specific authority ledger
- parallel Runtime or executor channel
- external-result claims

The dragon may inspect the card and paperwork. Runtime coordinates the route, and Court still keeps the vault key.