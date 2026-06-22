# Roadmap

## Phase 0: Doctrine and Contracts

- architecture and authority boundaries
- base agent and executor interfaces
- strict business intent schema
- structured handoff and result contracts
- receipt-aware local gateway skeleton

## Phase 1: Read-Only Operations

- scheduling observation
- CRM summaries
- inventory status
- invoice and receipt observation
- maintenance and equipment status
- reporting and alerts

## Phase 2: Low-Risk Approved Actions

- create internal tasks
- draft customer follow-up
- prepare booking proposals
- generate restock recommendations
- issue staff notifications

## Phase 3: Gated Business Actions

- booking changes
- CRM updates
- inventory adjustments
- approved invoicing operations
- purchasing requests
- access-control requests

## Phase 4: Physical Operations

Equipment and workshop automation come last. They require local presence rules, dedicated safety gates, bounded executors, cancel paths, and complete receipts.

## Public Release Checklist

- no credentials or private business data
- documented security model
- schema validation tests
- fail-closed examples
- replay protection
- clear separation between agents and executors
