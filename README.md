# Velvet Autonomous Business Agent Ecosystem

Offline-first, multi-agent business operations built around a strict separation of reasoning, authority, execution, and receipts.

> Brain proposes. Court authorizes. Agents coordinate. Executors act. Receipts remember.

## Purpose

This repository defines a reusable Velvet-style business autonomy framework for workshops, field services, inventory businesses, client operations, scheduling, invoicing, maintenance, and related business systems.

Agents reason and coordinate. They do not directly control business systems.

Executors perform one approved, bounded operation after identity, intent, policy, and safety checks succeed.

## Architecture

```text
human and business inputs
  -> Velvet Autonomy Gateway
  -> identity and intent schema
  -> Court policy gate
  -> safety check
  -> approved executor
  -> chained receipt log
```

See [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), the [Skill and Automation Trajectory](docs/skill_and_automation_trajectory.md), the [Engineering Quality Standard](docs/engineering_quality_standard.md), the [Protective and Operational Roles](docs/protective_and_operational_roles.md), and the [Procurement Authority Reconciliation](docs/procurement_authority_reconciliation.md).

## Working Vertical Slices

### Inventory review

A low-stock observation becomes a receipted internal review task. This flow cannot place an order, contact a vendor, move money, or modify inventory.

### Customer intake review

A customer request becomes a receipted internal review task. This flow cannot reply to the customer, send a quote, create a booking, sign a contract, or take payment.

### Durable job record

An approved intake review can become a durable internal job record through the Job Agent, job-record safety gate, human approval requirement, Court authorization, Job Executor, append-only job store, and receipt.

New jobs begin in `intake-review`. Their lifecycle is explicit:

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

Moving a job from `estimating` to `ready-to-schedule` now requires a stored estimate draft for that exact job:

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

The transition fails if the estimate is missing, belongs to another job, or the job state changed after authorization. The estimate remains an internal draft; readiness does not send a quote, book work, or claim customer acceptance.

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
  -> existing CourtPolicy and BusinessCoordinator
  -> dry-run executor
  -> Court authorization or denial receipt
  -> read-only evidence verifier
```

The immutable artifact binds supplier identity, supplier and manufacturer part numbers, quantity, currency, unit price, shipping, landed cost, destination reference, evidence, and review flags. Changing any sealed field changes the digest and therefore creates a different review subject.

The dry-run path proves that a reviewed procurement intent can travel through the same safety, Court, registry, one-use grant consumption, receipt, and verification chain as other business operations. The verifier checks that the approved intent, dry-run result, authorization receipt, authorization ID, authorization fingerprint, artifact ID, digest, handler ID, and `external_action: False` flag all agree.

This slice cannot contact a supplier, use payment credentials, place an order, spend funds, cancel or refund an order, or claim that an external result occurred. It verifies internal readiness only.

Run the current workshop demonstrations with:

```bash
python -m examples.small_workshop.demo
```

The demo uses `ChainedReceiptStore` by default. Without a signing key it runs in SHA-256 development mode. Set `VELVET_RECEIPT_SIGNING_KEY` to a key of at least 32 bytes to produce HMAC-SHA256 receipts.

## Shared Contracts

Business intents declare a risk level and approval mode. High-risk intents cannot request policy-only approval, and critical intents require strong human approval.

Agents may pass bounded context through structured handoffs, but a handoff carries no authority and performs no side effect.

The canonical runtime authority path remains `CourtPolicy` plus `BusinessCoordinator`. Court grants are short-lived, single-use, and bound to the complete business-intent fingerprint and optional principal session. Procurement extends this existing path rather than creating a parallel issuer or executor channel.

## Recommended Stores

Use `ChainedReceiptStore` for active business flows. It provides append-order verification, previous-receipt linking, deletion and reorder detection, optional HMAC-SHA256 authenticity, and local single-writer locking.

Use `JsonlJobStore` for the current durable job prototype. It records append-only creation and transition events, then reconstructs current state.

Use `JsonlEstimateStore` for immutable internal estimate drafts while the estimate and revision contracts stabilize.

Use `PreparedPurchaseArtifactStore` for immutable, canonical-digest procurement review artifacts. It stores prepared review evidence only and grants no purchasing authority.

Plain `JsonlReceiptStore` remains available for compatibility and focused tests.

## Status

Private architecture with working inventory, customer-intake, durable job-record, authority-gated transition, draft-only estimate, estimate-backed readiness, business summary, approval queue, and verified non-external procurement dry-run flows.

The procurement preparation, review, Court-intent bridge, safety gate, dry-run executor, authorization and denial receipts, and read-only evidence verifier are stable as internal proof points. Supplier contact, payment use, order placement, refunds, cancellation, receiving inspection, stock mutation from received goods, and external verification remain intentionally unimplemented.

The next implementation phase is receiving and verification design: define how a future received item would be checked against the approved artifact, supplier response, financial record, and receipt trail before any stock or job state changes.

## License

GPLv3. Part of the Velvet ecosystem.
