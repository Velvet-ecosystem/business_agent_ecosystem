# Skill and Automation Trajectory

This document defines how the Velvet business ecosystem grows from bounded local records into useful skills, external integrations, fabrication support, and carefully approved automation.

The goal is not to automate everything quickly. The goal is to make every new ability fit one shared structure so the ecosystem grows without fragmenting into unrelated bots, scripts, and platform-specific shortcuts.

## Shared skill contract

Every skill must declare:

- a stable identity and version,
- its owning domain,
- structured inputs and outputs,
- required capabilities and tools,
- read-only or state-changing behavior,
- approval mode,
- expected artifacts and receipts,
- failure, cancellation, and retry behavior,
- whether any external action is possible.

A skill may propose or prepare work. It does not inherit authority from the agent that invokes it. State changes and external actions must still pass through the capability registry, safety gate, authorization, bounded executor, verification, and receipt path.

## Domains

### Business operations

Read, summarize, prepare, and record work involving customers, jobs, invoices, payments, stock, communication history, change orders, and reports.

Current and near-term skills include:

- business daily brief,
- job status summary,
- customer history summary,
- outstanding invoice summary,
- attention and approval queue,
- decision recording and lineage,
- prepared customer follow-up,
- prepared job completion packet.

### Commerce channels

Shopify, eBay, Amazon, social platforms, and future storefronts are external channels, not the business source of truth.

Each platform must use a bounded adapter that translates platform records into Velvet contracts. Read-only ingestion and summaries come first. Drafting and preparation follow. Publishing, replying, listing changes, refunds, fulfilment changes, and other external actions remain approval-bound.

### Procurement and sourcing

Procurement serves production and operations through:

- bill-of-material requirements,
- supplier and component research,
- compatibility and counterfeit-risk checks,
- quote and landed-cost comparison,
- prepared purchase requests,
- immutable review artifacts,
- explicit human decisions,
- approved order placement,
- receiving inspection,
- stock and discrepancy records.

Finding a component never grants permission to purchase it. The final seller, part number, quantity, price, shipping destination, and payment impact must be reviewed before execution.

Current procurement maturity is non-executing:

```text
requirement
  -> supplier candidates
  -> comparison
  -> prepared purchase package
  -> immutable artifact + canonical digest
  -> exact artifact review request
  -> human decision
  -> decision-aware queue state
  -> decision lineage carrying artifact ID and digest
  -> immutable operation binding
  -> inert bounded record
```

Changing any sealed commercial field creates a different digest and therefore a different approval subject. This path cannot contact suppliers, access payment credentials, place an order, issue a Court grant, invoke an executor, or claim an external outcome.

### Foundry

Foundry skills support CAD, PCB design, slicing, enclosure work, wiring plans, and fabrication preparation.

Early Foundry skills should include:

- inspect CAD project,
- generate or validate a bill of materials,
- check clearances and manufacturability,
- prepare a 3D-print package,
- inspect a schematic,
- run ERC and DRC checks,
- prepare Gerbers, BOM, and pick-and-place files,
- prepare an enclosure from board dimensions,
- prepare a wiring-harness plan.

Design skills must produce reviewable artifacts, previews, diffs, and validation results. Sending a print job, ordering a PCB, controlling machinery, or purchasing components is a separate external action with stronger approval and safety requirements.

## Ecosystem-wide brief trajectory

The business daily brief is the first domain-specific proof of a broader Velvet brief pattern. The business implementation remains owned by the business domain, while a future shared brief contract allows other domains to contribute bounded summaries without exposing their internal stores directly.

Planned domain brief providers include:

- business operations,
- vehicle health and maintenance,
- medical monitoring and device readiness,
- security and cybersecurity,
- Foundry and machine readiness,
- continuity, integrity, backup, and recovery,
- home, mobile, and other enabled Velvet surfaces.

The shared composition path should be:

```text
shared brief contract
  -> permitted domain brief providers
  -> privacy, identity, and mode filtering
  -> owner-facing Velvet brief
```

Briefs remain read-only readers and composers. They may summarize, rank, and recommend attention, but they do not inherit execution authority and may not send, purchase, publish, unlock, drive, control machinery, or mutate domain state.

The ecosystem should support three brief classes:

1. **Domain briefs**: small summaries owned by one domain.
2. **Velvet composed brief**: an owner-facing composition of permitted domain summaries.
3. **Exception briefs**: focused alerts for urgent medical, security, vehicle-safety, integrity, or recovery conditions that should not wait for a scheduled brief.

Owner, guest, mobile, and remote views must receive different detail according to identity, context, privacy, and authentication strength. The composed brief must not become a central data warehouse or a shortcut around domain boundaries.

Promote this into an ecosystem-wide contract only after at least two non-business domain briefs prove that their contracts can remain small, deterministic, privacy-filtered, and read-only.

## Automation ladder

Every domain advances through the same stages:

1. **Observe**: read local or external state without changing it.
2. **Summarize**: produce a clear account of what exists.
3. **Recommend**: identify options, risks, and likely next actions.
4. **Prepare**: create a draft, package, design, comparison, or proposed change.
5. **Request approval**: present the exact bounded action and its consequences.
6. **Execute one bounded action**: perform only the approved operation.
7. **Verify**: confirm the external or local result matches the approval.
8. **Receipt and learn**: record what occurred and feed only approved lessons back into future work.

No skill may skip stages merely because a platform API, machine interface, or model makes the shortcut convenient.

## Integration pattern

The standard path is:

```text
agent or user request
  -> skill contract
  -> capability lookup
  -> policy and safety gate
  -> human approval when required
  -> canonical Court intent grant
  -> bounded executor or external adapter
  -> result verification
  -> durable record and receipt
```

External systems remain replaceable edges. Shopify, eBay, Amazon, social platforms, suppliers, board houses, printers, CAD tools, and workshop machines must not become the authority core.

The canonical runtime authority implementation is `CourtPolicy` plus `BusinessCoordinator`. Court grants are short-lived, single-use, and bound to the full `BusinessIntent` fingerprint and optional principal session. New domains must extend that path instead of creating parallel issuers or authorization stores.

## Build order

Completed or substantially proven:

1. shared contracts and bounded gateway architecture,
2. read-only business summaries,
3. approval and attention queue,
4. preparation-only business skills,
5. procurement requirements, supplier research, immutable review artifacts, decisions, and lineage,
6. non-executing integration proof from artifact through bounded matching.

Recommended next sequence:

1. reconcile procurement bindings with the existing Court intent-grant path,
2. add negative integration tests for denial, expiry, missing artifacts, route drift, action drift, handler drift, and digest drift,
3. define one exact procurement `BusinessIntent` schema and safety policy,
4. define verification and receipt requirements before adding an executor,
5. add Foundry inspection and fabrication-package skills,
6. add one commerce connector in read-only mode,
7. add tightly approved external actions one at a time,
8. add orchestration only after individual skills are proven,
9. consider limited autonomy only after repeated verified operation.

The ecosystem-wide composed brief belongs after multiple domain brief providers exist, not before them.

## Guardrails

- Local business records remain the source of truth.
- Agents coordinate but do not directly mutate systems.
- Skills do not bypass capability gates.
- Platform credentials grant transport access, not business authority.
- Purchasing, publishing, sending, refunds, financial actions, and machine operation require explicit bounded approval.
- Every external action must be verified and receipted.
- New domains reuse the shared framework rather than inventing parallel automation stacks.
- Deferred high-risk areas remain deferred until a concrete need, threat model, and approval design exist.
- Composed briefs remain read-only and privacy-filtered.
- Domain briefs expose bounded summaries, not unrestricted access to their stores.
- Procurement preparation records are evidence and lineage, not runtime authority.
- `CourtPolicy` remains the sole runtime issuer unless the authority layer is deliberately generalized for every domain.

## Direction

The next implementation milestone is not order placement. It is the authority-reconciliation and negative-testing pass documented in [Procurement Authority Reconciliation](procurement_authority_reconciliation.md).

The immediate proof target is:

```text
approved immutable procurement artifact
  -> one exact BusinessIntent containing artifact and lineage fields
  -> existing safety gate
  -> existing CourtPolicy
  -> existing BusinessCoordinator
  -> registered inert or simulated handler
  -> verified no-op receipt in tests
```

Only after this shared path is proven should the repository consider durable issuance details, an external supplier adapter, payment boundaries, order verification, or receiving workflows.

After multiple Velvet domains have proven read-only brief providers, promote a small shared brief contract and owner-facing composition layer at the ecosystem level.
