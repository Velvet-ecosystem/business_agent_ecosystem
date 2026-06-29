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

Initial skills should include:

- business daily brief,
- job status summary,
- customer history summary,
- outstanding invoice summary,
- attention and approval queue,
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
- approved order placement,
- receiving inspection,
- stock and discrepancy records.

Finding a component never grants permission to purchase it. The final seller, part number, quantity, price, shipping destination, and payment impact must be reviewed before execution.

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
  -> bounded executor or external adapter
  -> result verification
  -> durable record and receipt
```

External systems remain replaceable edges. Shopify, eBay, Amazon, social platforms, suppliers, board houses, printers, CAD tools, and workshop machines must not become the authority core.

## Build order

The recommended sequence is:

1. define the shared skill contract and loader,
2. add read-only business summaries,
3. add the approval and attention queue,
4. add preparation-only business skills,
5. add procurement records and supplier research,
6. add Foundry inspection and fabrication-package skills,
7. add one commerce connector in read-only mode,
8. add tightly approved external actions one at a time,
9. add orchestration only after individual skills are proven,
10. consider limited autonomy only after repeated verified operation.

## Guardrails

- Local business records remain the source of truth.
- Agents coordinate but do not directly mutate systems.
- Skills do not bypass capability gates.
- Platform credentials grant transport access, not business authority.
- Purchasing, publishing, sending, refunds, financial actions, and machine operation require explicit bounded approval.
- Every external action must be verified and receipted.
- New domains reuse the shared framework rather than inventing parallel automation stacks.
- Deferred high-risk areas remain deferred until a concrete need, threat model, and approval design exist.

## Direction

The next implementation milestone is a minimal skill framework proven by three read-only skills:

1. `business-daily-brief`,
2. `job-status-summary`,
3. `customer-history-summary`.

The first preparation skill should follow only after those contracts are stable. Commerce, procurement, and Foundry work then attach to the same framework in that order of risk, not as independent side projects.
