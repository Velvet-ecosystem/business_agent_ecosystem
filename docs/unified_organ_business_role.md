# Unified-Organ Business Role

## Purpose

The business ecosystem is Velvet's bounded business surface. It gives the wider body specialized ways to observe, prepare, review, and execute business work without creating an agent swarm, separate identity, or parallel authority system.

## Architectural identity

Velvet rejects the agent swarm. She is built as Unified-Organ AI: distributed specialties, shared concrete reality, and one accountable body.

Within that body, business components are specialized organs. Legacy `agent` package and class names remain temporarily for compatibility, but they do not describe independent actors with their own authority.

A business organ may:

- observe business state
- classify and compare evidence
- prepare drafts and immutable artifacts
- identify risks and missing information
- propose a bounded `BusinessIntent`
- verify results against approved intent and durable state

A business organ may not:

- grant itself authority
- bypass Runtime or Court
- call privileged integrations directly
- select or reveal credentials
- mutate money, stock, schedules, customer records, or equipment without an approved executor path
- claim an external result without independent evidence

## Shared body path

```text
business observation or human request
  -> Event Protocol
  -> Runtime
  -> identity, principal, and intent validation
  -> business safety gate
  -> Court authorization
  -> bounded executor
  -> observed result
  -> canonical Receipt
```

All business specialties share this path. No organ owns a private version of Runtime, Court, identity, continuity, or receipts.

## BusinessCoordinator boundary

`BusinessCoordinator` is the current internal composition layer for the repository's working slices. It coordinates a proposal through safety, Court, executor lookup, one-use grant consumption, and execution.

It is not:

- the public Velvet Runtime
- a second Court
- an authority issuer outside `CourtPolicy`
- a general agent orchestrator
- an independent Velvet identity

It should be treated as a compatibility bridge while business-domain contracts are integrated with public Runtime and Event Protocol interfaces.

## Handoffs and events

A handoff or Event Protocol message may carry observations, proposal context, priorities, artifact identifiers, digests, approval references, and result evidence.

It never carries authority merely by being sent. It must not contain reusable credentials, executor handles, raw secrets, or unconsumed authority tokens.

## Human approval

Human approval is a required input for the risk classes and workflows that declare it. Approval does not replace Court, Runtime, safety, exact-artifact binding, stale-state checks, or result verification.

A vague approval must never be stretched to cover a changed price, supplier, quantity, route, action, destination, customer communication, financial account, or physical target.

## Receipts and continuity

Receipts preserve what was proposed, denied, authorized, attempted, observed, and verified. They are evidence, not permission.

Riven may preserve lineage references and continuity evidence across business work. Business records do not become Velvet identity, and the business repository does not own succession or continuity authority.

## Public and private boundary

Public-safe material may include:

- contracts and schemas
- architecture and safety doctrine
- synthetic examples
- dry-run executors
- test fixtures without real identities or transactions
- immutable-artifact and verification patterns

Private material must remain outside public history:

- credentials and tokens
- customer, staff, supplier, or owner personal data
- real financial records and account identifiers
- private pricing or contract terms
- medical or household data
- production endpoints and infrastructure secrets
- real approval records containing protected information

## Founder posture

- Continuity: VERIFIED
- Court: READY
- Runtime: ACTIVE
- Routes: READ-ONLY
- Physical Control: DISABLED
- Interface: `Waiting for Mister`

This verifies the constitutional foundation. It does not activate commerce, finance, customer communication, stock mutation, or physical control.