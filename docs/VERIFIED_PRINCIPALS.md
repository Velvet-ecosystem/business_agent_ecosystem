# Verified Principals

`VerifiedPrincipal` is the durable identity contract for business actions.

It records:

- principal ID
- display name
- role
- authentication method
- presence level
- session ID
- verification time

`VerifiedBusinessCoordinator` is the canonical principal-aware execution entry point. It requires an explicit `VerifiedPrincipal`, validates that the identity ceremony is still fresh, binds the principal and session into the business context, then enters the normal safety, Court, executor, and Receipt path.

`PrincipalBusinessCoordinator` remains as a compatibility name for existing callers. It uses the same freshness validation and principal-binding helper; it is not a separate trust domain, authority path, or lower-assurance entry point.

The low-level `BusinessCoordinator` still receives a boolean internally after a principal-aware wrapper has enriched the context. That boolean is an implementation detail for existing slices, not a public authentication contract.

Production callers must pass a real `VerifiedPrincipal` created by the local identity ceremony. Stale principals fail closed before any proposal reaches Court.

Court grants bind to the exact intent, principal ID, and session ID. High-risk business organs derive actor identity from the verified principal rather than caller-supplied text.
