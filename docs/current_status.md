# Current Business Status

## Summary

The business-agent ecosystem currently has a safe internal operating spine and a verified procurement dry-run path.

The repository can model business work, prepare reviewable artifacts, route approved intents through the existing Court path, write local receipts, and verify that recorded evidence matches the approved intent.

It does not perform real-world procurement, commerce, supplier communication, financial activity, fulfilment, or stock changes from received goods.

## Proven internal slices

- inventory review tasks,
- customer intake review tasks,
- durable job records,
- authority-gated job transitions,
- internal estimate drafts,
- estimate-backed readiness,
- approval and attention queue,
- decision recording and lineage,
- immutable procurement artifacts,
- procurement intent bridge,
- procurement safety gate,
- dry-run procurement handler,
- authorization and denial receipts,
- read-only evidence verifier.

## Procurement maturity

The current procurement path is verified internal dry-run:

```text
requirement
  -> candidates
  -> comparison
  -> prepared package
  -> immutable artifact and digest
  -> review request
  -> human decision
  -> lineage
  -> BusinessIntent
  -> safety gate
  -> CourtPolicy
  -> BusinessCoordinator
  -> dry-run handler
  -> receipt
  -> verifier
```

The verifier checks that the approved intent, result, receipt, authorization id, authorization fingerprint, artifact id, digest, handler id, and no-real-world-effect flag all agree.

## Hard boundary

The following remain intentionally absent:

- real supplier contact,
- credential use,
- checkout or purchase behavior,
- fulfilment changes,
- refunds or cancellations,
- received-goods stock mutation,
- claims that a real-world result occurred.

## Next gate

The next milestone is receiving and verification design.

Before any connector can cause a real-world effect, the system needs contracts for:

- supplier response evidence,
- financial record evidence,
- delivered package evidence,
- inspection result evidence,
- discrepancy and quarantine decisions,
- stock update eligibility,
- receipts for each step.

Only after those contracts are stable should the repository consider any real-world connector.
