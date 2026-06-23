# Principal-Bound Court Grants

Court authorizations can now bind to both an exact intent and a verified actor session.

A principal-bound grant records:

- exact intent fingerprint
- principal ID
- session ID
- issue time
- expiry time

Consumption succeeds only when the exact same intent, principal ID, and session ID are presented before expiry. Actor drift, session drift, replay, mutation, and expiration fail closed.

The standard coordinator reads reserved principal context fields and supplies them during grant issue and consumption. Principal-bound runs receive a separate Court `authorized` receipt containing the actor and session binding.

Legacy callers without principal context continue to receive intent-only grants temporarily so existing slices and tests remain compatible. New high-risk flows should use `VerifiedBusinessCoordinator` and principal-derived agents.
