# Architecture

The business ecosystem is a bounded business surface within Velvet's **Unified-Organ AI** architecture.

It is not an agent swarm, a separate Velvet identity, or a parallel Runtime. Legacy `agent` names remain in packages and classes for compatibility, but their architectural role is that of bounded business organs.

## 1. Inputs and observations

Human, business, identity, and environmental inputs enter through bounded adapters.

Examples include:

- voice and touch UI
- manager dashboard
- staff mobile companion
- bookings, tasks, CRM, inventory, forms, email, cameras, sensors, and equipment status
- NFC, local touch, voice phrase, physical presence, and role clearance

Inputs are observations or requests. They do not carry authority by themselves.

## 2. Event Protocol and Runtime

Business observations, requests, proposals, decisions, results, and lifecycle events travel through Event Protocol-compatible contracts.

Runtime owns production execution coordination. It validates routes, state, capability availability, and execution posture before consequential work can proceed.

The current internal `BusinessCoordinator` composes the working business-domain path for local prototypes and tests. It is a compatibility bridge beneath the Runtime contract, not a replacement Runtime.

## 3. Business organs

Business organs own bounded specialties such as intake, inventory review, estimating, scheduling preparation, procurement preparation, receiving verification, and release review.

They may:

- observe
- reason
- prioritize
- prepare artifacts
- compare evidence
- propose a bounded `BusinessIntent`

They may not:

- grant authority
- select or expose credentials
- bypass Runtime or Court
- call privileged integrations directly
- claim an external result without verification

Structured handoffs carry context, not authority.

## 4. Authority pipeline

```text
business observation or human request
  -> Event Protocol
  -> Runtime
  -> identity, principal, and BusinessIntent validation
  -> business safety gate
  -> Court authorization
  -> bounded executor
  -> observed result
  -> canonical Receipt
```

Every consequential action follows this path. Missing identity, intent, Runtime route, safety, Court authorization, executor, or receipt infrastructure causes privileged work to fail closed.

## 5. Court and bounded grants

Court is the authority layer. Grants are:

- short-lived
- single-use
- bound to the complete intent fingerprint
- optionally bound to principal and session
- rejected after expiry, replay, actor drift, or intent mutation

No business domain may introduce a second issuer, authority ledger, or parallel grant-consumption channel.

## 6. Executors

Executors own narrow integrations with scheduling, CRM, inventory, invoicing, notifications, access control, reporting, maintenance, purchasing, customer follow-up, and future equipment operations.

Each executor performs one bounded operation with validated parameters and must return an observable result suitable for verification and receipting.

An executor does not decide whether it should run.

## 7. Receipts and continuity

Receipts preserve evidence of proposals, denials, authorizations, execution attempts, results, and discrepancies. A Receipt is evidence, never permission.

The public `velvet-receipts` contract is canonical. Local stores in this repository are implementations and prototypes that must remain compatible with that contract.

Riven may preserve lineage references and continuity evidence across business activity, but this repository does not own Velvet identity, succession, or continuity authority.

## 8. Hardware and network foundation

The system is local-first, wired where practical, cloud-optional, and explicit about node identity and trust.

Remote access may observe or request. It does not equal verified local presence and does not create authority.

## Core distinction

```text
Business organ = observes, reasons, prepares, and proposes.
Runtime = coordinates execution posture and routes.
Court = authorizes or denies bounded capability.
Executor = performs one approved operation.
Receipt = preserves evidence.
Riven = preserves continuity lineage, not business authority.
```

## Founder baseline

- Continuity: VERIFIED
- Court: READY
- Runtime: ACTIVE
- Routes: READ-ONLY
- Physical Control: DISABLED
- Interface: `Waiting for Mister`

Current business flows remain internal and non-external under this baseline.