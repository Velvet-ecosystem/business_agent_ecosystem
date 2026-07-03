# Procurement Authority Reconciliation

## Decision

The existing gateway authority implementation is the canonical Court path for procurement and every other business domain.

Procurement must extend `business_agents.gateway.authority.CourtPolicy` and `business_agents.gateway.coordinator.BusinessCoordinator`. It must not introduce a second issuer, parallel authorization ledger, or executor bypass.

## Existing Court properties

`CourtPolicy` already provides:

- fail-closed identity and safety requirements,
- a deterministic SHA-256 fingerprint over the complete `BusinessIntent`,
- route, action, subject, parameters, risk, and approval-mode binding,
- short-lived grants,
- optional principal and session binding,
- one-use consumption,
- replay rejection,
- expiry rejection,
- intent-mutation rejection,
- actor-drift rejection.

`BusinessCoordinator` already provides the standard runtime order:

```text
agent proposal
  -> safety evaluation
  -> Court evaluation
  -> authorization receipt
  -> executor lookup
  -> one-use grant consumption
  -> executor invocation
```

Denied, missing, invalid, expired, or unavailable paths fail closed and produce receipts where appropriate.

## Procurement preparation boundary

The procurement slice currently stops before Court issuance. It provides:

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

The immutable procurement artifact must become part of the canonical `BusinessIntent.parameters` before Court evaluation. The intended integration shape is:

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
  -> normal safety evaluation
  -> normal CourtPolicy evaluation
  -> normal short-lived intent grant
  -> normal coordinator consumption
  -> one registered procurement executor
```

Because `intent_fingerprint()` includes the complete parameters mapping, any change to supplier, part, quantity, price, currency, destination, artifact digest, handler, approval request, or decision lineage must produce a different fingerprint and invalidate the original grant.

## Relationship to the bounded record

The current bounded record is an inert contract and test fixture, not a second authorization system.

Before execution work begins, choose one of these implementations:

1. **Preferred:** treat the bounded record as a typed procurement payload embedded in the canonical `BusinessIntent.parameters`, while `CourtPolicy` remains the sole runtime issuer and one-use grant store.
2. Generalize `AuthorizationGrant` to carry a typed immutable binding shared by all domains, while retaining one Court and one coordinator.

Do not persist or consume a separate procurement grant beside `CourtPolicy` unless the canonical authority layer is deliberately refactored for every domain.

## Required work before external execution

1. Add negative integration tests for denial, missing artifacts, changed route, changed action, changed handler, changed digest, and expiry.
2. Define the exact procurement `BusinessIntent` schema and safety policy.
3. Bind the final handler through the existing executor registry.
4. Re-read the immutable artifact immediately before execution.
5. Verify the artifact digest and all commercial fields against the approved intent.
6. Add supplier-response and financial-result verification.
7. Write chained receipts for authorization, attempted execution, verified outcome, and any discrepancy.
8. Add explicit revocation and recovery behavior without creating a second authority store.

## Deferred capabilities

The following remain intentionally absent:

- supplier contact,
- payment credential access,
- order placement,
- refunds or cancellation,
- record consumption service,
- procurement-specific Court issuer,
- procurement-specific authority ledger,
- external result claims.

The dragon may inspect the card and paperwork. The canonical Court still keeps the vault key.
