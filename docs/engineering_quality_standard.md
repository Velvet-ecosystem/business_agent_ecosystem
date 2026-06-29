# Engineering Quality Standard

Velvet is not defined by how quickly code can be generated. It is defined by whether its behavior can be understood, reviewed, tested, constrained, recovered, and trusted.

This standard applies to human-written, AI-assisted, generated, imported, and adapted contributions equally. Generation method is never evidence of correctness.

## Core rule

No feature is complete because it runs once. A feature is complete only when its contract, authority boundary, failure behavior, tests, documentation, and operational limits are visible.

## Architecture before expansion

Every substantial feature must identify:

- the responsibility it owns,
- the domain and layer where it belongs,
- its inputs and outputs,
- the state it may read or change,
- its capability and approval requirements,
- its external-action boundary,
- its verification and receipt path,
- its safe failure and recovery behavior.

New features must extend existing contracts when appropriate. They must not create parallel authority, receipt, identity, or integration systems for convenience.

## Change discipline

Changes should be small enough to review honestly. Each pull request should have one clear purpose, describe affected authority or state boundaries, and avoid unrelated cleanup.

A change must not hide behavior in prompts, model assumptions, implicit globals, undocumented environment state, or platform-specific side effects.

Generated code must be treated as untrusted draft material until reviewed against repository contracts and tests.

## Testing tiers

### Contract tests

Prove schemas, identifiers, routes, actions, approval modes, and module boundaries remain stable.

### Unit tests

Prove isolated calculations, validation, parsing, state transitions, and failure cases.

### Integration tests

Prove the complete bounded path across proposal, capability lookup, safety gate, authorization, executor, durable state, and receipt.

### Negative and fail-closed tests

Prove malformed, stale, mismatched, unauthorized, duplicate, and out-of-scope requests are rejected before mutation or external action.

### Recovery tests

Prove interrupted operations, corrupted records, unavailable connectors, and restart conditions return to a known safe state.

### Hardware and external-system tests

Use simulation or fixtures first. Real machinery, financial systems, publishing, purchasing, customer communication, and platform mutations require explicit test plans, bounded credentials, rollback procedures, and human supervision.

Coverage percentage alone is not a quality claim. Tests must protect meaningful invariants.

## Review requirements

Reviewers should be able to answer:

1. What new behavior exists?
2. Who or what may invoke it?
3. What authority does it require?
4. What can it change?
5. How does it fail closed?
6. How is the result verified?
7. Where is the receipt or durable evidence?
8. How is it disabled or recovered?

Changes that cannot answer these questions are not ready to merge.

## Dependency policy

Dependencies must have a clear purpose, compatible license, maintained source, bounded permissions, and acceptable offline behavior.

Prefer small, auditable libraries and standard-library solutions where practical. Avoid adding a framework merely to remove a few lines of local code.

Versions should be constrained deliberately. Dependency updates require test evidence and review of security, API, behavior, and licensing changes.

No secret, credential, private endpoint, generated token, or personal data may be committed to the repository.

## Security and privacy review

Features involving identity, credentials, external connectors, customer data, financial records, network access, machine control, or public communication require an explicit security and privacy review.

The review must consider least privilege, data minimization, retention, redaction, credential rotation, audit evidence, abuse cases, and containment.

Transport access is not business authority. A valid API token does not permit an agent to take any action not independently authorized by Velvet policy.

## Documentation requirements

A new capability, skill, connector, store, machine adapter, or officer responsibility must document:

- purpose and non-goals,
- ownership and boundaries,
- inputs and outputs,
- approval and risk level,
- external effects,
- failure behavior,
- test coverage,
- known limitations,
- operational and recovery notes.

Documentation must describe current behavior, not aspirations disguised as completed features.

## Release stages

### Experimental

The contract is still changing. Simulation and local development only. No reliance for real business, financial, customer, or machine decisions.

### Prototype

The bounded flow works and has meaningful tests, but interfaces, storage, and recovery behavior may still change.

### Pilot

Used in a limited real setting with supervision, constrained credentials, backups, monitoring, and a rollback path.

### Stable

Contracts are documented, migrations and recovery are tested, security review is complete, operational limits are known, and repeated pilot use has produced verified results.

### Production-ready

This label is permitted only when the actual deployment environment has completed threat review, backup and restore testing, observability, incident procedures, dependency review, credential management, rollback planning, and sustained supervised operation.

Repository maturity alone does not make a deployment production-ready.

## Release gate

Before a feature advances in maturity, it must have:

- a stable contract,
- reviewed authority boundaries,
- meaningful positive and negative tests,
- CI success,
- documented limitations,
- receipt or audit evidence where applicable,
- recovery or rollback behavior,
- no unresolved critical security findings,
- an explicit owner for maintenance.

## Quality signals

Public quality is shown through evidence:

- readable architecture,
- focused pull requests,
- visible CI,
- invariant-based tests,
- threat and failure analysis,
- explicit limitations,
- reproducible demonstrations,
- traceable releases,
- honest maturity labels,
- durable receipts.

Claims such as intelligent, autonomous, secure, safe, or production-ready must be supported by defined behavior and evidence.

## AI-assisted development

AI may help research, draft, review, test, refactor, and document. It does not receive an exemption from engineering discipline.

AI-generated contributions must be checked for invented APIs, duplicated logic, insecure defaults, excessive dependencies, hidden network assumptions, incorrect edge cases, license contamination, and tests that merely restate the implementation.

The repository should preserve the useful speed of modern tools without outsourcing judgment to them.

## Standing principle

Fast drafting is welcome. Fast authority growth is not.

Velvet should stand out not because it contains more generated code, but because every important path has an owner, a boundary, a test, a gate, a recovery plan, and a receipt.
