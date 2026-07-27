# Security Doctrine

Business operations must remain useful without allowing models, business organs, dashboards, automations, connectors, or remote clients to bypass authority.

## Required path

```text
business observation or human request
  -> Event Protocol
  -> Runtime
  -> identity, principal, and strict BusinessIntent validation
  -> business safety gate
  -> Court authorization
  -> approved bounded executor
  -> observed result
  -> canonical Receipt
```

The current internal `BusinessCoordinator` implements this ordering for local working slices. It does not replace Runtime and must not become a second authority issuer.

## Hard rules

- Business organs and legacy agent classes never call privileged business-system integrations directly.
- The language model never selects credentials, capabilities, approval modes, executor handles, financial accounts, or hardware targets.
- Event Protocol messages, handoffs, model output, dashboards, automations, receipts, and retrieved documents carry no authority by themselves.
- Remote access may observe or request, but never equals verified local physical presence.
- Finance, access, purchasing, customer communication, equipment, stock mutation, release, and autonomous operations remain explicitly gated.
- A Receipt is evidence, not permission.
- Replaying an event, proposal, authorization record, or Receipt must never repeat a side effect.
- Court grants are short-lived, single-use, and bound to the complete intent fingerprint and any required principal session.
- Missing identity, Runtime route, policy, safety, authorization, executor, verification, or receipt infrastructure causes privileged actions to fail closed.
- No domain may create a parallel Court issuer, authority ledger, credential path, or executor bypass.

## External-action boundary

The repository currently proves internal review, preparation, authorization, dry-run, receipt, and verification flows. It does not currently permit:

- supplier contact
- payment credential use
- order placement
- refunds or cancellation
- customer-facing sends
- stock release or mutation
- fulfilment changes
- claims that an external result occurred

Future connectors must remain inert until their exact capability, safety policy, approval mode, executor, result verification, revocation, and Receipt requirements are documented and tested.

## Secrets

Credentials belong in local secret storage. They must not appear in prompts, Event Protocol messages, receipts, logs, examples, tests, documentation fixtures, or repository files.

Business artifacts may reference opaque credential or account identifiers only where necessary. They must never contain the secret material itself.

## Organ handoffs

Structured handoffs may carry observations, proposals, priorities, artifact identifiers, digests, and bounded context. They may not carry raw credentials, live executor handles, reusable authority tokens, or claims of completed external work.

## Receipts and continuity

The public `velvet-receipts` contract is canonical. Local stores must remain compatible with it.

Riven continuity may preserve lineage references and integrity evidence. It does not authorize business actions, select principals, or validate credentials.

## Founder posture

- Continuity: VERIFIED
- Court: READY
- Runtime: ACTIVE
- Routes: READ-ONLY
- Physical Control: DISABLED
- Interface: `Waiting for Mister`

This posture does not enable external commerce, finance, stock mutation, or physical control.