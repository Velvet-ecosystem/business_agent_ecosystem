# Architecture

The ecosystem follows six layers.

## 1. Inputs

Human, business, and identity inputs enter through bounded adapters.

Examples:

- voice and touch UI
- manager dashboard
- staff mobile companion
- bookings, tasks, CRM, inventory, forms, email, cameras, sensors, and equipment status
- NFC, local touch, voice phrase, physical presence, and role clearance

## 2. Velvet Autonomy Gateway

The local gateway contains:

- Velvet orchestration
- offline language and reasoning
- business memory and continuity
- agent-mesh coordination

The language model does not directly control business systems or hardware.

## 3. Authority Pipeline

```text
identity check
  -> strict intent schema
  -> Court policy gate
  -> safety check
  -> approved executor
  -> receipt log
```

Every meaningful action passes through this path.

## 4. Agent Ecosystem

Agents own bounded business roles and coordinate through structured handoffs.

Agents may plan, reason, prioritize, and propose. They may not perform privileged side effects directly.

## 5. Executors

Executors own integrations with scheduling, CRM, inventory, invoicing, notifications, access control, reporting, maintenance, purchasing, customer follow-up, and future equipment operations.

Each executor performs a narrow operation with validated parameters.

## 6. Hardware and Network Foundation

The system is local-first, wired where practical, cloud-optional, and explicit about node identity and trust.

## Core Distinction

```text
Agent = reasons and proposes.
Court = authorizes.
Executor = performs one bounded operation.
Receipt = preserves evidence.
```
