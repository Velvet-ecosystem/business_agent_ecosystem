# Velvet Business Operations Ecosystem

Offline-first business operations for Velvet, built as a bounded business surface within **Unified-Organ AI**.

> Business organs observe, reason, and propose. Runtime coordinates. Court authorizes. Executors act. Receipts remember.

## Purpose

This repository defines a reusable Velvet-style business operations framework for workshops, field services, inventory businesses, client operations, scheduling, estimating, maintenance, procurement preparation, and related business systems.

The repository retains legacy `agent` package and class names for compatibility. Architecturally, those components are bounded business organs. They may reason, prioritize, prepare artifacts, and submit proposals. They do not hold authority and do not directly control business systems.

Executors perform one approved, bounded operation only after identity, intent, policy, safety, and authorization checks succeed.

## Place in Velvet

This repository is not a second Velvet, a second Runtime, or an independent authority system.

- `velvet-event-protocol` carries observations, requests, proposals, results, and lifecycle events.
- `velvet-runtime` owns production execution coordination.
- Court grants or denies bounded authority.
- This repository owns business-domain contracts, organs, safety gates, internal stores, review flows, and bounded executors.
- `velvet-receipts` owns the canonical receipt contract; local receipt stores here are implementations and prototypes that must remain compatible with it.
- Riven continuity may preserve lineage references, but this repository does not own Velvet identity or succession.

## Constitutional Path

```text
business observation or human request
  -> Event Protocol
  -> Runtime
  -> identity, principal, and BusinessIntent validation
  -> business safety gate
  -> Court authorization
  -> bounded business executor
  -> observed result
  -> canonical Receipt
```

The current internal `BusinessCoordinator` composes proposal, safety, Court, executor-registry, authorization-consumption, and receipt steps for the working slices in this repository. It is a business execution coordinator and compatibility bridge. It is not the ecosystem Runtime and must not become a parallel authority issuer.

See [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), [Unified-Organ Business Role](docs/unified_organ_business_role.md), [Current Status](docs/current_status.md), [Skill and Automation Trajectory](docs/skill_and_automation_trajectory.md), [Engineering Quality Standard](docs/engineering_quality_standard.md), [Protective and Operational Roles](docs/protective_and_operational_roles.md), and [Procurement Authority Reconciliation](docs/procurement_authority_reconciliation.md).

## Working Vertical Slices

### Inventory review

A low-stock observation becomes a receipted internal review task. This flow cannot place an order, contact a vendor, move money, or modify inventory.

### Customer intake review

A customer request becomes a receipted internal review task. This flow cannot reply to the customer, send a quote, create a booking, sign a contract, or take payment.

### Durable job record

An approved intake review can become a durable internal job record through the Job Agent, job-record safety gate, human approval requirement, Court authorization, Job Executor, append-only job store, and receipt.

New jobs begin in `intake-review`:

```text
intake-review
  -> approved
  -> estimating
  -> ready-to-schedule
  -> scheduled
  -> in-progress
  -> completed
```

A job may be cancelled from any non-terminal working state. Completed and cancelled jobs are terminal.

### Authority-gated job transitions

Job state changes travel through a dedicated proposal, safety, authorization, execution, and receipt path. Normal working-state transitions are medium risk and require human approval. Moving a job to `completed` or `cancelled` is high risk and requires strong human approval.

The executor re-reads durable state immediately before mutation and rejects stale authorizations when the stored state no longer matches the state declared in the proposal.

### Internal estimate draft

A job already in `estimating` can produce a durable internal estimate draft. Estimate arithmetic uses decimal values and two-place monetary rounding. The safety gate independently verifies component totals and rejects customer-facing or transactional fields.

An estimate draft is not a customer quote. It cannot send itself, collect acceptance, alter a contract, schedule work, or take payment.

### Estimate-backed readiness

Moving a job from `estimating` to `ready-to-schedule` requires a stored estimate draft for that exact job:

```text
estimating job + estimate reference
  -> Estimate Readiness Agent
  -> estimate-readiness safety gate
  -> human approval
  -> Court authorization
  -> executor re-reads job and estimate stores
  -> exact job/estimate binding check
  -> ready-to-schedule transition and receipt
```

The transition fails if the estimate is missing, belongs to another job, or the job state changed after authorization. Readiness does not send a quote, book work, or claim customer acceptance.

### Procurement review, Court path, and verified dry-run

The current procurement slice is deliberately non-external:

```text
requirement
  -> supplier candidates
  -> comparison
  -> prepared purchase package
  -> immutable artifact + canonical digest
  -> exact artifact review request
  -> explicit human decision
  -> decision-aware review state
  -> lineage package carrying the same artifact and digest
  -> canonical procurement BusinessIntent
  -> procurement safety gate
  -> internal BusinessCoordinator compatibility bridge
  -> Court authorization or denial
  -> dry-run executor
  -> canonical Receipt
  -> read-only evidence verifier
```

The immutable artifact binds supplier identity, supplier and manufacturer part numbers, quantity, currency, unit price, shipping, landed cost, destination reference, evidence, and review flags. Changing any sealed field changes the digest and creates a different review subject.

This slice cannot contact a supplier, use payment credentials, place an order, spend funds, cancel or refund an order, mutate stock, or claim that an external result occurred.

Run the current workshop demonstrations with:

```bash
python -m examples.small_workshop.demo
```

The demo uses `ChainedReceiptStore` by default. Without a signing key it runs in SHA-256 development mode. Set `VELVET_RECEIPT_SIGNING_KEY` to a key of at least 32 bytes to produce HMAC-SHA256 receipts.

## Shared Contracts

Business intents declare a risk level and approval mode. High-risk intents cannot request policy-only approval, and critical intents require strong human approval.

Bounded organs may pass structured context through handoffs or Event Protocol messages, but a handoff carries no authority and performs no side effect.

Court grants are short-lived, single-use, and bound to the complete business-intent fingerprint and optional principal session. No business domain may create a parallel issuer, authority ledger, or executor channel.

## Recommended Stores

Use `ChainedReceiptStore` for active business flows while maintaining compatibility with the canonical public Receipt contract. It provides append-order verification, previous-receipt linking, deletion and reorder detection, optional HMAC-SHA256 authenticity, and local single-writer locking.

Use `JsonlJobStore` for the current durable job prototype, `JsonlEstimateStore` for immutable internal estimate drafts, and `PreparedPurchaseArtifactStore` for immutable procurement review artifacts. None of these stores grants authority.

Plain `JsonlReceiptStore` remains available for compatibility and focused tests.

## Verified Founder Posture

- Continuity: VERIFIED
- Court: READY
- Runtime: ACTIVE
- Routes: READ-ONLY
- Physical Control: DISABLED
- Interface: `Waiting for Mister`

The repository's current business slices remain internal, local-first, review-oriented, and non-external under this posture.

## Status

Private architecture with working inventory, customer-intake, durable job-record, authority-gated transition, draft-only estimate, estimate-backed readiness, business summary, approval queue, receiving-evidence, release-review, and verified non-external procurement dry-run flows.

Supplier contact, payment use, order placement, refunds, cancellation, stock mutation, stock release execution, and external-result verification remain intentionally unimplemented.

## License

GPLv3. Part of the Velvet ecosystem.