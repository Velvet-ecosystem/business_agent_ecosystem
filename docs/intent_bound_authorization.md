# Intent-Bound Authorization

Court approvals are now unique, one-use grants bound to the exact approved intent.

The fingerprint covers:

- route
- action
- subject identifier
- canonicalized parameters

Before execution, the coordinator consumes the authorization and verifies the current intent matches the stored fingerprint. Reuse, mutation, or an unknown authorization fails closed.

Successful executor receipts preserve both the authorization identifier and the 64-character SHA-256 intent fingerprint.

```text
proposal
  -> safety
  -> Court issues unique grant + intent fingerprint
  -> executor route resolves
  -> Court consumes and verifies grant
  -> executor acts
  -> receipt preserves grant and fingerprint
```
