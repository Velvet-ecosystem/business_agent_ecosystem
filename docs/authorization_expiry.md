# Authorization Expiry

Court authorization grants are short-lived as well as one-use and intent-bound.

By default, a grant expires 30 seconds after issuance. The lifetime is configurable when constructing `CourtPolicy`, but must always be positive.

Each grant records:

- authorization identifier
- intent fingerprint
- issued timestamp
- expiry timestamp

Expired grants fail closed and are removed automatically during Court evaluation, grant-count inspection, or explicit cleanup. Tests use an injected clock so expiry behavior is deterministic and does not depend on real-time sleeping.

Successful executor receipts preserve the grant's issued and expiry timestamps for audit.
