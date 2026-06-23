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

See [ARCHITECTURE.md](ARCHITECTURE.md) and [SECURITY.md](SECURITY.md).

## Working Vertical Slices

### Inventory review

A low-stock observation becomes a receipted internal review task:

```text
inventory context
  -> Inventory Agent proposal
  -> internal-task safety gate
  -> Court identity and policy decision
  -> Task Executor
  -> chained receipt
```

This flow cannot place an order, contact a vendor, move money, or modify inventory.

### Customer intake review

A customer request becomes a receipted internal review task:

```text
customer request
  -> Intake Agent proposal
  -> internal-task safety gate
  -> Court identity and policy decision
  -> Task Executor
  -> chained receipt
```

This flow cannot reply to the customer, send a quote, create a booking, sign a contract, or take payment. It captures bounded context and creates an internal task for human review.

### Durable job record

An approved intake review can become a durable internal job record:

```text
approved intake context
  -> Job Agent proposal
  -> job-record safety gate
  -> human approval requirement
  -> Court authorization
  -> Job Executor
  -> append-only job store and receipt
```

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

A job may be cancelled from any non-terminal working state. Completed and cancelled jobs are terminal. Jobs cannot skip lifecycle states, and job creation cannot include quote totals, schedules, signatures, messages, or payment data.

### Internal estimate draft

A job already in `estimating` can produce a durable internal estimate draft:

```text
estimating job and pricing inputs
  -> Estimate Agent calculation
  -> estimate-draft safety gate
  -> human approval requirement
  -> Court authorization
  -> Estimate Executor
  -> append-only estimate store and receipt
```

Estimate arithmetic uses decimal values and two-place monetary rounding. The draft records labour, materials, contingency, margin, tax, and total. The safety gate independently verifies the component sum, rejects negative or non-finite values, applies a bounded maximum, and refuses customer-message, quote-send, payment-link, signature, or scheduling fields.

An estimate draft is not a customer quote. It cannot send itself, collect acceptance, alter a contract, schedule work, or take payment.

Run the current workshop demonstrations with:

```bash
python -m examples.small_workshop.demo
```

The demo uses `ChainedReceiptStore` by default. Without a signing key it runs in SHA-256 development mode. Set `VELVET_RECEIPT_SIGNING_KEY` to a key of at least 32 bytes to produce HMAC-SHA256 receipts.

## Shared Contracts

Business intents declare a risk level and approval mode. High-risk intents cannot request policy-only approval, and critical intents require strong human approval.

Agents may pass bounded context through structured handoffs, but a handoff carries no authority and performs no side effect.

## Recommended Stores

Use `ChainedReceiptStore` for active business flows. It adds:

- append-order verification
- previous-receipt linking
- deletion and reorder detection
- optional HMAC-SHA256 authenticity
- local single-writer locking

Use `JsonlJobStore` for the current durable job prototype. It records append-only creation and transition events, then reconstructs the current state.

Use `JsonlEstimateStore` for immutable internal estimate drafts while the estimate and revision contracts stabilize.

Plain `JsonlReceiptStore` remains available for compatibility and focused tests.

## Status

Early private architecture with working inventory, customer-intake, durable job-record, and draft-only estimate contract flows.

## License

GPLv3. Part of the Velvet ecosystem.
