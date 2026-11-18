# Department Workflows and Model-Neutral Coordination

Status: **initial contract and read-only proof**, not a deployed workforce or active external automation service.

## Purpose

The business surface should work as a coordinated set of departments: one researches a client need, the next researches distributors, the next checks manufacturers and provenance, then commercial analysis produces a comparison, sales prepares a draft, and an independent reviewer prepares a packet for human decision.

This adopts the useful department-and-handoff *pattern* from multi-agent maps, not their software, vendor lock-in, or agent count. One model or deterministic worker can perform several bounded skills. Quality, evidence, turnaround, and accountability matter more than the number of bots.

## Separation of responsibilities

- **Workflow planner:** tracks workflow run, stage ownership, prerequisites, blocked work, and handoff readiness. The initial planner is entirely in memory and never runs a model or external action.
- **Commander Velour (future business coordination role):** a delegated business desk responsible for dividing jobs among departments, tracking research artifacts and continuity, and sending completed packages to Velvet and the owner. Velvet can delegate business workloads to free her for vehicle, home, and other domains; Velour never becomes a second Runtime, Court, or independent grant issuer. GPT may assist Velour with reasoning when connected and authorized, but the model is not the workflow's source of truth or execution authority.
- **Intelligence provider:** GPT is the owner's preferred reasoning/research provider for authorized online work, accessed through a future replaceable adapter. Velvet's native AI or another explicitly approved model can perform a task when appropriate, especially offline. No provider integration exists in this first slice. A ChatGPT subscription must not be treated as an automatically connected background/API service; runtime access, privacy controls and any separate API billing must be verified before integration.
- **Velvet Event Protocol + Runtime:** production coordination, routes, operational posture and state.
- **Court and existing business safety gates:** sole authorization boundary. The existing BusinessCoordinator is a compatibility bridge for approved business execution, not this workflow planner.
- **Bounded executor and Receipt:** one exact approved action, observed result, independent verification, canonical receipt. Workflow messages never carry authority, credentials, or executor handles.

## Starter business departments

| Stage | Department | Output |
| --- | --- | --- |
| 1 | Intake | Client requirements and explicit research scope |
| 2 | Client research | Source-backed client research brief, open questions |
| 3 | Distributor sourcing | Distributor shortlist with dated evidence |
| 4 | Manufacturer due diligence | Origin, part numbers, genuine supplier, compatibility and risk evidence |
| 5 | Commercial comparison | Currency, quantity, delivery and landed-cost comparison |
| 6 | Sales preparation | Internal proposal draft; no external sending |
| 7 | Independent quality review | Evidence, privacy, claims and disclosure review packet |

A workflow can branch and later join; dependent work remains blocked until every required input is available. Follow-on departments may include marketing, operations, inventory, after-sales support, finance, and commerce, but only after their contracts are proven.

## First working slice

The module business_agents/workflow_handoffs.py introduces:

- WorkflowStage: stable stage ID, owning department, expected output kind, predecessor stage IDs.
- WorkflowPlan: a per-run, deterministic directed acyclic graph. It rejects duplicate stages, missing dependencies, cycles, and self-dependencies.
- WorkflowArtifactRef: workflow-bound stage and artifact IDs, type, SHA-256 field, and source evidence *references* rather than raw customer data.
- WorkflowHandoff: exact ordered inputs to one ready department, containing no token or permission.
- ready_stages: discovers uncompleted work with satisfied prerequisites.
- make_handoff / validate_handoff: rejects stale or changed predecessor references and wrong-workflow handoffs.
- accept_artifact: returns a new in-memory mapping only for a ready stage of the expected output kind; no persistence or action.
- example_sourcing_plan: a seven-step fictional client/distributor/manufacturer sourcing workflow.

The nine accompanying tests cover ordered transfer, drift, type/duplicate rejection, missing or cyclic dependencies, invalid digests, cross-client isolation, independent branches and joins, and absence of execution methods.

**Important limit:** a correctly formed SHA-256 string is not proof that the original artifact was stored, independently hashed, verified, or factually correct. The caller currently supplies references. Before production, a trusted artifact layer must retrieve immutable content, recompute its digest, check provenance, ACL, freshness, classification and run ownership, and record verification receipts.

## Source and provider boundaries

A website, PDF, email or model reply is untrusted data, never instructions. Research must distinguish cited evidence, unverified claims, model inferences, and missing facts. Hosted models may receive only authorized, minimum-necessary context and must be blocked by default when offline or data disclosure is disallowed. Do not put real client names, supplier relationships, confidential prices, tokens, or private transaction history in this public repository or fixtures. Private intelligence belongs in velvet-business-smarts and approved vault storage.

Provider ID, model version, input artifact refs, output digest, privacy decision, costs, outcome, and evidence should eventually be logged through compatible lifecycle events and receipts. No model may choose authority scope, issue grants, change approval mode, reveal credentials or invoke privileged tools directly.

Human approval of an internal review package is **not** permission to email a customer, purchase components, alter a storefront, publish marketing, schedule work, or change inventory. Those actions each require an exact BusinessIntent, policy/safety validation, Runtime/Court route, bounded executor, result verification and Receipt. Existing procurement remains non-external.

## Future Founder capability tree

A business dashboard could display each run's department stages, evidence refs, blocked reasons, review decisions, failures and cost/latency. Later status words may include locked, ready, working, needs-evidence, needs-review, proposed, approved, executed, verified and failed. The current module only computes readiness, not those workflow statuses, and never claims that other stages are implemented.

## Ordered build plan

1. **This PR:** pure in-memory planner, reference handoffs, sourcing example and negative tests.
2. Add durable run state, immutable artifact store integration, independent digest verification, data classification, source timestamps, cancellation, retry/idempotency, stale-source checks and canonical Receipts.
3. Integrate a model-neutral SkillRunner through existing Runtime, starting with a fake deterministic worker. Add output schema validation, hard budgets, privacy gates, model/provider selection, failure isolation and a real source verifier.
4. Trial an entirely fictional client-to-manufacturer research package and owner review packet. Then allow approved read-only private data sources for a single real pilot.
5. Build Founder/mobile visibility and additional department branches. Add a consequential executor only when existing authority tests prove the complete safe path.

This work must not become an agent swarm, a second Runtime/Court, an all-access central data warehouse, or a new automation path that bypasses the existing ecosystem.
