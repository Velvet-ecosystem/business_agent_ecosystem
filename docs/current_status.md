# Current Business Status

## Summary

The business-agent ecosystem currently has a safe internal operating spine, a verified procurement dry-run path, a receiving verification chain for future goods intake evidence, stock eligibility decision records, and human release review records.

The repository can model business work, prepare reviewable artifacts, route approved intents through the existing Court path, write local receipts, verify procurement dry-run evidence, verify receiving evidence consistency, record stock eligibility decisions, and record explicit human release reviews.

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
- read-only receiving chain verifier,
- stock eligibility decision records,
- human release review records.

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

The current receiving path is verified evidence consistency plus explicit release review:

```text
receiving evidence
  -> inspection record
  -> optional quarantine record
  -> read-only receiving verifier
  -> stock eligibility decision
  -> human release review
```

Receiving evidence records what is claimed to have arrived. Inspection records compare received evidence against expected values and produce matched, needs-review, or rejected status. Quarantine records hold non-matched review or rejection reasons.

The receiving verifier checks that evidence, inspection, and quarantine records agree on artifact id, evidence id, inspection id, quantity, supplier part number, manufacturer part number, findings, and quarantine reason codes.

Matched inspections must not have quarantine. Non-matched inspections must have quarantine. Every receiving layer reports `eligible_for_stock = False`.

Stock eligibility decisions can record eligible, not-eligible, or review-required status from a receiving verification result. Every stock eligibility decision reports `mutates_stock = False`.

Release review records can record approved, denied, or needs-more-evidence status. They require an explicit human decision and always report `mutates_stock = False` and `executes_release = False`.

## Hard boundary

The following remain intentionally absent:

- real supplier contact,
- credential use,
- checkout or purchase behavior,
- fulfilment changes,
- refunds or cancellations,
- stock release execution,
- received-goods stock mutation,
- claims that a real-world result occurred.

## Next gate

The next milestone is authority-gated release intent design, not stock mutation.

Before any stock mutation is possible, the system still needs contracts for:

- exact release review binding,
- canonical release intent,
- release safety gate,
- Court authorization,
- immutable release receipt,
- inventory mutation proposal,
- mutation safety gate,
- post-mutation verification.

Only after those contracts are stable should the repository consider stock mutation or any real-world connector.
