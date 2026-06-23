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

`PrincipalBusinessCoordinator` requires a verified principal and enriches agent context with reserved principal fields.

The old `identity_verified=True` path remains available only through an explicitly marked legacy principal. It is a compatibility bridge, not a production authentication mechanism.

Production callers should pass a real `VerifiedPrincipal` created by the local identity ceremony.

The next migration step is to bind Court grants and successful executor receipts directly to the principal and session, then remove caller-supplied actor names from work-start and other high-risk intents.
