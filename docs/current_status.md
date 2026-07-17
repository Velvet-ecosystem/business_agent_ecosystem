# Current Business Status

## Summary

The business-agent ecosystem currently has a safe internal operating spine, a verified procurement dry-run path, and a receiving verification chain for future goods intake evidence.

The repository can model business work, prepare reviewable artifacts, route approved intents through the existing Court path, write local receipts, verify procurement dry-run evidence, and verify receiving evidence consistency.

It does not perform real-world procurement, commerce, supplier communication, financial activity, fulfilment, stock release, or stock changes from received goods.

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
- read-only procurement evidence verifier,
- receiving evidence records,
- receiving inspection records,
- receiving quarantine records,
- read-only receiving chain verifier.

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

The procurement verifier checks that the approved intent, result, receipt, authorization id, authorization fingerprint, artifact id, digest, handler id, and no-real-world-effect flag all agree.

## Receiving maturity

The current receiving path is verified evidence consistency:

```text
receiving evidence
  -> inspection record
  -> optional quarantine record
  -> read-only receiving verifier
```

Receiving evidence records what is claimed to have arrived. Inspection records compare received evidence against expected values and produce matched, needs-review, or rejected status. Quarantine records hold non-matched review or rejection reasons.

The receiving verifier checks that evidence, inspection, and quarantine records agree on artifact id, evidence id, inspection id, quantity, supplier part number, manufacturer part number, findings, and quarantine reason codes.

Matched inspections must not have quarantine. Non-matched inspections must have quarantine. Every receiving layer reports `eligible_for_stock = False`.

## Hard boundary

The following remain intentionally absent:

- real supplier contact,
- credential use,
- checkout or purchase behavior,
- fulfilment changes,
- refunds or cancellations,
- stock release,
- received-goods stock mutation,
- claims that a real-world result occurred.

## Next gate

The next milestone is stock eligibility design, not stock mutation.

Before any received item can become eligible for inventory, the system needs contracts for:

- supplier response evidence,
- financial record evidence,
- exact approval artifact binding,
- receiving-chain verification result,
- separate release review,
- stock eligibility decision,
- receipts for each step.

Only after those contracts are stable should the repository consider stock mutation or any real-world connector.
