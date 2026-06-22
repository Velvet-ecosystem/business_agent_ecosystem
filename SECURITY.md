# Security Doctrine

Business autonomy must remain useful without allowing agents, models, dashboards, or remote clients to bypass authority.

## Required Path

```text
input
  -> identity and context
  -> strict intent schema
  -> Court policy
  -> safety check
  -> approved executor
  -> receipt
```

## Hard Rules

- Agents never call business-system integrations directly.
- The language model never selects credentials, capabilities, or hardware targets.
- Remote access may observe or request, but never equals verified local physical presence.
- Finance, access, purchasing, equipment, and autonomous operations remain explicitly gated.
- A receipt is evidence, not permission.
- Replaying an event or receipt must never repeat a side effect.
- Missing identity, policy, safety, or receipt infrastructure causes privileged actions to fail closed.

## Secrets

Credentials belong in local secret storage. They must not appear in prompts, events, receipts, logs, examples, or repository files.

## Agent Handoffs

Agent-to-agent messages may carry observations, proposals, priorities, and bounded context. They may not carry raw credentials, executor handles, or authority tokens.
