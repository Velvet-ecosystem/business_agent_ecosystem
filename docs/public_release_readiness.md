# Public Release Readiness

This repository is an alpha-stage, local-first business operations framework. Public release does not mean production authority or external commerce is enabled.

See [Public Release Verification](public_release_verification.md) for the current evidence record and the remaining owner-controlled visibility steps.

## Safe public scope

Public-safe material includes:

- business intent and proposal contracts;
- safety gates and bounded executors;
- dry-run procurement and receiving verification;
- immutable artifact, digest, and lineage patterns;
- idempotency and external-operation reconciliation;
- synthetic examples and tests;
- Unified-Organ AI business architecture.

## Material that stays private

Do not publish:

- credentials, tokens, signing keys, or local secret stores;
- real customer, supplier, employee, financial, medical, or owner-policy data;
- private operating records and archives;
- deployment addresses, network details, or hardware-specific secrets;
- production connector configuration.

## Current capability boundary

The repository may model work, prepare artifacts, request review, run internal bounded slices, and demonstrate deterministic in-memory adapters. It does not currently provide production supplier contact, purchasing, payment, refunds, stock mutation, stock release, customer delivery, or physical control.

## Release gate

Before changing repository visibility, confirm:

- package metadata and Python requirements are accurate;
- the complete test suite passes on a clean Python 3.11+ environment;
- no generated runtime data or local secrets are tracked;
- all open pull requests are reconciled against current `main`;
- examples contain synthetic identities and addresses only;
- Runtime, Court, Event Protocol, Receipts, and Riven boundaries remain explicit;
- external actions remain idempotent, journalled, and fail closed;
- the README status matches actual implemented capabilities;
- a full Git-history secret scan has completed;
- repository security settings have been reviewed before visibility changes.

## Founder compatibility

The current public architecture baseline remains:

- Continuity: VERIFIED
- Court: READY
- Runtime: ACTIVE
- Routes: READ-ONLY
- Physical Control: DISABLED
- Interface: `Waiting for Mister`

Business code in this repository must not reinterpret that posture as permission to execute external or physical effects.
