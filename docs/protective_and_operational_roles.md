# Protective and Operational Roles

This document defines the responsibilities that protect and coordinate the Velvet business ecosystem. These are responsibilities first. They may begin as modules, skills, gates, or services and become separate agents only when separation of authority, workload, or safety requires it.

## Doorman

Owns entry, identity, session scope, and routing.

Responsibilities:

- identify the requester, device, connector, or agent,
- verify permitted authentication factors,
- establish a bounded session,
- assign role and context scope,
- route requests to the correct domain,
- reject unknown, malformed, or out-of-scope entry,
- record the entry decision.

The Doorman decides who may enter and where they may go. It does not authorize the requested business action.

## Security Officer

Owns authority behavior, policy abuse detection, and escalation.

Responsibilities:

- inspect capability and approval requests,
- detect privilege escalation and role misuse,
- detect suspicious action sequences,
- identify repeated failed or bypassed approvals,
- require stronger approval,
- suspend a session, skill, connector, or agent when policy permits,
- open and preserve a security incident record.

The Security Officer asks whether behavior remains inside granted authority.

## Cybersecurity Officer

Owns technical trust and cyber risk.

Responsibilities:

- review exposed services and network paths,
- audit credentials, secrets, and connector scopes,
- check dependencies and known vulnerability risks,
- detect configuration drift and tampering indicators,
- review authentication failures and unusual API activity,
- verify patch, backup, and recovery posture,
- quarantine technical connectors through bounded procedures,
- preserve technical incident evidence.

Cybersecurity does not replace business authorization. A technically valid token still carries no authority beyond approved policy.

## Data and Privacy Steward

Owns data minimization, access, retention, redaction, export, and deletion rules.

Responsibilities:

- classify business and personal data,
- limit collection to declared purposes,
- control context sharing between skills and agents,
- define retention and deletion schedules,
- redact sensitive material from logs and artifacts,
- review external data transfers,
- record privacy decisions and exceptions.

## Workflow Coordinator

Owns sequencing, dependencies, pause, resume, and duplicate prevention.

Responsibilities:

- track the state of multi-step work,
- route approved handoffs,
- wait on missing inputs or approval,
- prevent duplicate execution,
- resume interrupted work from a verified checkpoint,
- expose blocked and overdue tasks.

The Workflow Coordinator carries no independent execution authority.

## Quality Officer

Owns output validation before real-world consequence.

Responsibilities:

- verify names, identifiers, quantities, totals, attachments, and references,
- compare prepared output against its request and approval,
- inspect CAD dimensions, tolerances, manufacturability, ERC, and DRC results,
- identify incomplete or inconsistent artifacts,
- reject work that cannot be verified,
- record review evidence.

Quality review must remain independent from the component that created the output when consequence is significant.

## Machine Safety Officer

Owns physical safety for printers, CNC equipment, test rigs, relays, power systems, and workshop machinery.

Responsibilities:

- verify machine identity and safe configuration,
- check interlocks, workspace state, operator presence, and emergency stop readiness,
- enforce bounded operating envelopes,
- reject unsafe commands or unavailable safeguards,
- place equipment into a known safe state,
- record machine-operation evidence and incidents.

Machine safety is separate from cybersecurity and from design quality.

## Auditor and Compliance Officer

Owns independent review of whether policy, approval, evidence, retention, licensing, and operational requirements were followed.

Responsibilities:

- inspect receipts and approval chains,
- review policy and process compliance,
- check platform, contractual, licensing, and retention obligations,
- identify missing or contradictory evidence,
- issue findings without changing the records under review.

The Auditor does not perform or approve the action it audits.

## Records Steward

Owns durable linkage and discoverability of records, artifacts, revisions, approvals, and receipts.

Responsibilities:

- preserve append-only history,
- link results to their source request and approval,
- maintain revision and lineage information,
- index artifacts without granting access beyond policy,
- detect missing or orphaned records,
- support verified export and restoration.

## Continuity and Recovery Officer

Owns backup, restoration, degraded operation, and return to safe service.

Responsibilities:

- define backup and restore procedures,
- test restoration rather than assuming it,
- detect corrupted or incomplete state,
- coordinate safe restart and connector recovery,
- rotate credentials through approved procedures,
- maintain rollback and disaster-recovery plans,
- record continuity exercises and real incidents.

## Integration Steward

Owns connector contracts and health for commerce, social, supplier, CAD, board-house, and machine integrations.

Responsibilities:

- maintain API versions and schemas,
- enforce least-privilege scopes,
- monitor rate limits and connector health,
- translate external records into internal contracts,
- isolate platform-specific behavior,
- disable or degrade safely when an external platform changes.

External platforms remain replaceable edges, not sources of authority.

## Standard request path

```text
request or event
  -> Doorman
  -> bounded session and route
  -> skill proposal
  -> Security and Cybersecurity inspection as required
  -> Data and Privacy checks as required
  -> Court and safety gate
  -> Workflow coordination
  -> bounded executor or adapter
  -> Quality or Machine Safety verification
  -> durable record and receipt
  -> independent audit and continuity support
```

Not every request invokes every role. The risk, data, external effects, and physical consequences determine which checks apply.

## Separation principles

- Entry is not authorization.
- Authentication is not business authority.
- Coordination is not execution.
- Creation is not quality approval.
- Technical access is not policy permission.
- Audit is not mutation.
- Security is not recovery.
- Cybersecurity is not machine safety.
- A role name does not require a separate personality or model.

## Initial implementation order

1. Doorman contracts for identity, session scope, and routing.
2. Security inspection for capability and privilege requests.
3. Records and workflow support for approvals and incidents.
4. Data and privacy classification for customer and connector data.
5. Cybersecurity checks for credentials, exposure, and configuration drift.
6. Quality checks for business and Foundry artifacts.
7. Continuity and recovery exercises.
8. Machine safety only when physical execution is introduced.
9. Independent audit checks across the completed paths.

This ordering establishes protection and evidence before broad automation or physical authority grows.
