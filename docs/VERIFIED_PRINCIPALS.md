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

`PrincipalBusinessCoordinator` now requires an explicit `VerifiedPrincipal` for every public execution. The synthetic `identity_verified=True` compatibility bridge and legacy principal factory have been removed.

The low-level `BusinessCoordinator` still receives a boolean internally after a principal-aware wrapper has enriched the context. That boolean is an implementation detail for existing slices, not a public authentication contract.

Production callers must pass a real `VerifiedPrincipal` created by the local identity ceremony.

Court grants bind to the exact intent, principal ID, and session ID. High-risk agents derive actor identity from the verified principal rather than caller-supplied text.
