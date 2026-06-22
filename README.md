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

## First Working Flow

The first vertical slice turns a low-stock observation into a receipted internal review task:

```text
inventory context
  -> Inventory Agent proposal
  -> internal-task safety gate
  -> Court identity and policy decision
  -> Task Executor
  -> chained receipt
```

Run the demonstration with:

```bash
python -m examples.small_workshop.demo
```

The demo now uses `ChainedReceiptStore` by default. Without a signing key it runs in SHA-256 development mode. Set `VELVET_RECEIPT_SIGNING_KEY` to a key of at least 32 bytes to produce HMAC-SHA256 receipts.

This flow cannot place an order, contact a vendor, move money, or modify inventory. It creates only an approved internal review task.

## Recommended Receipt Store

Use `ChainedReceiptStore` for active business flows. It adds:

- append-order verification
- previous-receipt linking
- deletion and reorder detection
- optional HMAC-SHA256 authenticity
- local single-writer locking

Plain `JsonlReceiptStore` remains available for compatibility and focused tests.

## Status

Early private architecture and working contract framework.

## License

GPLv3. Part of the Velvet ecosystem.
